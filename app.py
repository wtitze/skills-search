import streamlit as st
import psycopg2
import hashlib
import redis
import os
import time
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURAZIONI ---
st.set_page_config(page_title="Knowledge Brain v6.12", layout="wide")
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# --- INIZIALIZZAZIONE ---
@st.cache_resource
def get_ai_engines():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = OllamaLLM(model="llama3.1:8b", temperature=0)
    v_client = QdrantClient(url="http://localhost:6333")
    if not v_client.collection_exists("knowledge_brain"):
        v_client.create_collection("knowledge_brain", vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
    vector_store = QdrantVectorStore(client=v_client, collection_name="knowledge_brain", embedding=embeddings)
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    return vector_store, llm, redis_client

with st.sidebar:
    vector_store, llm, redis_client = get_ai_engines()

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

def add_to_history(user_id, query):
    key = f"history:{user_id}"
    last = redis_client.lindex(key, 0)
    if last is None or last.decode('utf-8') != query:
        redis_client.lpush(key, query)
        redis_client.ltrim(key, 0, 4)

def get_history(user_id):
    key = f"history:{user_id}"
    return [q.decode('utf-8') for q in redis_client.lrange(key, 0, -1)]

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("🧠 Knowledge Brain: Login")
    with st.form("login_form"):
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.form_submit_button("Accedi"):
            conn = get_sql_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, sede FROM users WHERE username=%s AND password=%s", (u_in, p_in))
            res = cur.fetchone()
            conn.close()
            if res:
                st.session_state.user = {"id": res[0], "nome": res[1], "sede": res[2]}
                st.rerun()
            else: st.error("Credenziali errate")
    st.stop()

u = st.session_state.user
st.sidebar.title(f"👤 {u['nome']}")
st.sidebar.write(f"📍 {u['sede']}")
st.sidebar.divider()
st.sidebar.subheader("🕒 Ultime ricerche")
for h in get_history(u['id']):
    st.sidebar.info(h)
if st.sidebar.button("Esci"):
    st.session_state.clear()
    st.rerun()

st.title("🧠 Portale Competenze Aziendali")
tab1, tab2 = st.tabs(["🔍 Ricerca Esperti", "📤 Gestione Dati"])

# --- TAB 2: CARICAMENTO ---
with tab2:
    st.header("Upload Documentazione")
    mode = st.radio("Attribuzione:", ["Propria", "Terzi"], horizontal=True)
    if 'up_key' not in st.session_state: st.session_state.up_key = 3000
    up_files = st.file_uploader("Seleziona PDF o TXT", accept_multiple_files=True, key=f"up_{st.session_state.up_key}")
    
    if st.button("🚀 Inizia Indicizzazione") and up_files:
        conn = get_sql_conn()
        cur = conn.cursor()
        for f in up_files:
            try:
                content = f.read()
                f_hash = hashlib.md5(content).hexdigest()
                f_path = os.path.abspath(os.path.join(UPLOAD_DIR, f.name))
                with open(f_path, "wb") as out: out.write(content)
                cur.execute("INSERT INTO documents (user_id, filename, file_hash) VALUES (%s, %s, %s)", (u['id'], f.name, f_hash))
                text = ""
                if f.name.endswith('.pdf'):
                    reader = PdfReader(f_path)
                    for page in reader.pages: text += page.extract_text()
                else: text = content.decode("utf-8")
                owner = u['nome'] if mode == "Propria" else "DA ESTRARRE"
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                docs = [Document(page_content=c, metadata={"owner_name": owner, "file_path": f_path}) for c in splitter.split_text(text)]
                vector_store.add_documents(docs)
            except: pass
        conn.commit()
        conn.close()
        st.session_state.up_key += 1
        st.success("Operazione conclusa.")
        time.sleep(1)
        st.rerun()

# --- TAB 1: RICERCA OTTIMIZZATA ---
with tab1:
    with st.form("search_form", clear_on_submit=False):
        query = st.text_input("Quale competenza o informazione cerchi?")
        submitted = st.form_submit_button("🔍 Analizza Competenze")

    if submitted and query:
        add_to_history(u['id'], query)
        with st.status("Analisi in corso...", expanded=False):
            expansion = llm.invoke(f"Sei un assistente tecnico. Elenca 3 termini o brand strettamente correlati a '{query}'. Solo parole separate da virgola.")
            results = vector_store.similarity_search(f"{query}, {expansion}", k=8)
            context = "\n\n".join([f"FONTE: {d.metadata.get('file_path')}\nPROPRIETARIO: {d.metadata.get('owner_name')}\nTESTO: {d.page_content}" for d in results])

        st.subheader("Risultato dell'Analisi")
        prompt = f"""Sei un consulente HR senior. Analizza il contesto aziendale e risolvi la domanda.
        
        REGOLE CRITICHE DI FILTRO:
        1. SELEZIONE: Identifica SOLO i migliori candidati (massimo 2 o 3). 
        2. RIGORE: Se un candidato nel contesto non ha attinenza DIRETTA con la tecnologia o la sede richiesta, IGNORALO completamente. Non elencare profili non idonei.
        3. ORDINE: Elenca per primo il profilo più pertinente.
        4. MOTIVAZIONE: Spiega in due righe perché è la scelta ideale, citando brand o certificazioni.
        5. FONTE: Cita sempre il percorso del file.
        6. Se non ci sono match di qualità, scrivi: "Nessun esperto interno risponde ai requisiti richiesti."
        
        DOMANDA: {query}
        CONTESTO: {context}
        
        RISPOSTA (Stile sintetico per dirigenti):
        """
        placeholder = st.empty()
        full_res = ""
        for chunk in llm.stream(prompt):
            full_res += chunk
            placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        st.session_state.last_answer = full_res

    elif 'last_answer' in st.session_state:
        st.divider()
        st.subheader("Ultimo Risultato")
        st.markdown(st.session_state.last_answer)
