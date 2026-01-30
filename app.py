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
st.set_page_config(page_title="Knowledge Brain v6.6", layout="wide")
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# --- UI INIZIALE IMMEDIATA ---
st.title("🧠 Knowledge Brain: Enterprise Agent")

if 'system_ready' not in st.session_state:
    with st.spinner("🚀 Caricamento motori IA in corso... attendere prego."):
        st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        v_client = QdrantClient(url="http://localhost:6333")
        if not v_client.collection_exists("knowledge_brain"):
            v_client.create_collection("knowledge_brain", vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
        st.session_state.vector_store = QdrantVectorStore(client=v_client, collection_name="knowledge_brain", embedding=st.session_state.embeddings)
        st.session_state.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        st.session_state.system_ready = True
        st.rerun()

vector_store = st.session_state.vector_store
llm = st.session_state.llm
redis_client = st.session_state.redis_client

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

# --- LOGIN ---
if 'user' not in st.session_state:
    with st.container():
        st.subheader("🔐 Accesso")
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Login"):
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
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

tab1, tab2 = st.tabs(["🔍 Ricerca Esperti", "📤 Gestione Documentale"])

# --- TAB CARICAMENTO ---
with tab2:
    st.header("Upload")
    mode = st.radio("Chi è il proprietario di questi file?", ["Io (" + u['nome'] + ")", "Un altro collaboratore (estrai dal testo)"])
    if 'up_key' not in st.session_state: st.session_state.up_key = 200
    up_files = st.file_uploader("Trascina file qui", type=['pdf', 'txt'], accept_multiple_files=True, key=f"up_{st.session_state.up_key}")
    
    if st.button("🚀 Indicizza ora") and up_files:
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
                
                owner = u['nome'] if "Io" in mode else "DA ESTRARRE"
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                docs = [Document(page_content=c, metadata={"owner_name": owner, "file_path": f_path}) for c in splitter.split_text(text)]
                vector_store.add_documents(docs)
                st.success(f"✅ {f.name} salvato.")
            except: st.warning(f"⚠️ {f.name} già presente.")
        conn.commit()
        conn.close()
        st.session_state.up_key += 1
        time.sleep(1)
        st.rerun()

# --- TAB RICERCA ---
with tab1:
    query = st.text_input("Quale competenza o informazione cerchi?")
    if query:
        with st.spinner("Consultazione base di conoscenza..."):
            results = vector_store.similarity_search(query, k=5)
            context = "\n\n".join([f"FONTE: {d.metadata.get('file_path')}\nPROPRIETARIO: {d.metadata.get('owner_name')}\nTESTO: {d.page_content}" for d in results])

            prompt = f"""
            Sei un assistente HR sintetico e professionale. Rispondi alla DOMANDA usando SOLO il CONTESTO.
            
            REGOLE OBBLIGATORIE:
            1. Sii brevissimo. Rispondi solo con Nome, Sede e il motivo tecnico.
            2. Se nel contesto vedi 'PROPRIETARIO: NomeCognome', quella persona è l'unico esperto di quel testo, anche se il suo nome non appare nel 'TESTO'.
            3. Se 'PROPRIETARIO: DA ESTRARRE', identifica il nome leggendo il 'TESTO'.
            4. Se la domanda riguarda un'attività non tecnica o non presente (es. organizzare feste, compiti non professionali), rispondi: "Non è stato trovato nessun esperto interno per questa specifica richiesta."
            5. Per ogni persona trovata, cita il file: "Fonte: [file_path]".
            6. NON spiegare le regole di ragionamento. NON mostrare termini tecnici come 'owner_name' o 'metadata'.
            
            DOMANDA: {query}
            CONTESTO: {context}
            
            RISPOSTA:
            """
            
            st.subheader("Risultato")
            placeholder = st.empty()
            full_res = ""
            for chunk in llm.stream(prompt):
                full_res += chunk
                placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
