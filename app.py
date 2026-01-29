import streamlit as st
import psycopg2
import hashlib
import redis
import time
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURAZIONI ---
st.set_page_config(page_title="Knowledge Brain v5.1", layout="wide")

def initialize_system():
    if 'system_ready' not in st.session_state:
        with st.status("🚀 Inizializzazione Motore IA...", expanded=True) as status:
            st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            st.session_state.llm = OllamaLLM(model="llama3.2")
            v_client = QdrantClient(url="http://localhost:6333")
            st.session_state.vector_store = QdrantVectorStore(client=v_client, collection_name="knowledge_brain", embedding=st.session_state.embeddings)
            st.session_state.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            st.session_state.system_ready = True
            status.update(label="✅ Sistema Pronto!", state="complete", expanded=False)
            st.rerun()

if 'system_ready' not in st.session_state:
    initialize_system()
    st.stop()

vector_store = st.session_state.vector_store
llm = st.session_state.llm
redis_client = st.session_state.redis_client

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

def add_to_history(user_id, query):
    key = f"history:{user_id}"
    redis_client.lpush(key, query)
    redis_client.ltrim(key, 0, 9)

def get_history(user_id):
    key = f"history:{user_id}"
    return [q.decode('utf-8') for q in redis_client.lrange(key, 0, -1)]

if 'user' not in st.session_state:
    st.title("🔐 Accesso Knowledge Brain")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            try:
                conn = get_sql_conn()
                cur = conn.cursor()
                cur.execute("SELECT id, nome, sede FROM users WHERE username=%s AND password=%s", (username, password))
                res = cur.fetchone()
                conn.close()
                if res:
                    st.session_state.user = {"id": res[0], "nome": res[1], "sede": res[2]}
                    st.rerun()
                else:
                    st.error("Credenziali errate")
            except Exception as e: st.error(f"Errore DB: {e}")
    st.stop()

u = st.session_state.user
st.sidebar.title(f"👤 {u['nome']}")
st.sidebar.subheader("🕒 Ultime Ricerche")
for h in get_history(u['id']):
    st.sidebar.caption(f"• {h}")
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

st.title("🧠 Knowledge Brain Agent v5.1")
tab1, tab2 = st.tabs(["🔍 Ricerca Esperti", "📤 Carica Conoscenza"])

with tab2:
    st.header("Carica i tuoi aggiornamenti")
    up_file = st.file_uploader("Carica un file di testo", type=['txt'])
    if up_file:
        content = up_file.read()
        f_hash = hashlib.md5(content).hexdigest()
        text = content.decode("utf-8")
        try:
            conn = get_sql_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO documents (user_id, filename, file_hash) VALUES (%s, %s, %s)", (u['id'], up_file.name, f_hash))
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(text)
            docs = [Document(page_content=c, metadata={"user_id": u['id'], "user_name": u['nome'], "source": up_file.name}) for c in chunks]
            vector_store.add_documents(docs)
            conn.commit()
            conn.close()
            st.success("Conoscenza integrata!")
        except Exception: st.warning("Documento già presente.")

with tab1:
    col_in, col_res = st.columns([4, 1])
    with col_in:
        query = st.text_input("Cosa stai cercando?", key="search_input")
    with col_res:
        st.write(" ")
        if st.button("🗑️ Reset"):
            st.session_state.executed_query = ""
            st.rerun()

    if query and query != st.session_state.get('executed_query', ''):
        st.session_state.executed_query = query
        add_to_history(u['id'], query)
        
        with st.spinner("L'Agente sta filtrando i profili..."):
            results = vector_store.similarity_search(query, k=6)
            context = "\n".join([f"[CANDIDATO: {d.metadata.get('user_name')}] {d.page_content}" for d in results])
            
            # PROMPT POTENZIATO CON REFLECTION RIGOROSA
            prompt = f"""
            Sei un esperto selezionatore tecnico (HR Tech).
            
            RICHIESTA UTENTE: "{query}"
            
            CANDIDATI ESTRATTI DALLA MEMORIA:
            {context}
            
            ISTRUZIONI PER LA RIFLESSIONE (CRITICO):
            1. Analizza i candidati uno per uno.
            2. Se la richiesta è per "iOS", includi SOLO chi lavora esplicitamente su iOS/Swift. 
            3. SCARTA categoricamente chi si occupa di Android, Flutter o Backend se non hanno anche competenze iOS esplicite nel testo fornito.
            4. Se non trovi nessuno che corrisponde ESATTAMENTE alla tecnologia richiesta, dichiara che non ci sono esperti per quella specifica tecnologia.
            5. Non inventare motivazioni: usa solo i fatti presenti nel testo.
            
            STRUTTURA RISPOSTA:
            - Introduzione sintetica.
            - Elenco puntato degli esperti VALIDI (Nome - Sede - Motivo tecnico).
            - Se hai scartato profili simili (es. Android invece di iOS), spiega brevemente perché non sono stati inclusi nel risultato principale.
            """
            
            st.subheader("Risposta dell'Agente")
            placeholder = st.empty()
            full_res = ""
            for chunk in llm.stream(prompt):
                full_res += chunk
                placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
