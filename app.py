import streamlit as st
import psycopg2, hashlib, redis, os, json, time, re, ast
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURAZIONI ---
st.set_page_config(page_title="Knowledge Brain Gold v10.0", layout="wide")
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

@st.cache_resource
def get_ai_engines():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = OllamaLLM(model="llama3.1:8b", temperature=0)
    v_client = QdrantClient(url="http://localhost:6333")
    col_name = "knowledge_brain"
    if not v_client.collection_exists(col_name):
        v_client.create_collection(col_name, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
    vector_store = QdrantVectorStore(client=v_client, collection_name=col_name, embedding=embeddings)
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    return vector_store, llm, redis_client

with st.sidebar:
    with st.spinner("Avvio motori IA..."):
        vector_store, llm, redis_client = get_ai_engines()

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

def get_top_tags():
    try:
        conn = get_sql_conn(); cur = conn.cursor()
        cur.execute("""
            SELECT s.name, COUNT(us.user_id) as freq FROM skills s 
            JOIN user_skills us ON s.id = us.skill_id 
            GROUP BY s.name ORDER BY freq DESC LIMIT 12
        """)
        res = cur.fetchall(); conn.close()
        return res
    except: return []

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("🧠 Knowledge Brain: Enterprise Login")
    with st.form("login"):
        u_in = st.text_input("Username"); p_in = st.text_input("Password", type="password")
        if st.form_submit_button("Accedi"):
            conn = get_sql_conn(); cur = conn.cursor()
            cur.execute("SELECT id, nome, sede FROM users WHERE username=%s AND password=%s", (u_in, p_in))
            res = cur.fetchone(); conn.close()
            if res: st.session_state.user = {"id": res[0], "nome": res[1], "sede": res[2]}; st.rerun()
            else: st.error("Accesso negato")
    st.stop()

u = st.session_state.user
st.sidebar.title(f"👤 {u['nome']}")

# --- SIDEBAR TAGS ---
st.sidebar.divider()
st.sidebar.subheader("🏷️ Competenze in Database")
for tag, count in get_top_tags():
    if st.sidebar.button(f"{tag} ({count})", key=f"btn_{tag}", use_container_width=True):
        st.session_state.active_tag = tag

if st.sidebar.button("Logout", type="secondary"):
    st.session_state.clear(); st.rerun()

st.title("🧠 Portale Management Competenze")
tab1, tab2 = st.tabs(["🔍 Ricerca Esperti", "📤 Ingestion"])

# --- TAB INGESTION ---
with tab2:
    st.header("Caricamento Documentazione")
    mode = st.radio("Metodo di attribuzione:", ["Automatico (Proprietà: " + u['nome'] + ")", "Analisi Testo (HR Mode)"], horizontal=True)
    if 'up_key' not in st.session_state: st.session_state.up_key = 0
    up_files = st.file_uploader("Seleziona PDF", accept_multiple_files=True, key=f"u_{st.session_state.up_key}")
    
    if st.button("🚀 Avvia Ingestion") and up_files:
        conn = get_sql_conn(); cur = conn.cursor()
        ing_log = []
        for f in up_files:
            try:
                f_path = os.path.abspath(os.path.join(UPLOAD_DIR, f.name))
                with open(f_path, "wb") as out: out.write(f.read())
                reader = PdfReader(f_path)
                text = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
                
                o_id, o_name = u['id'], u['nome']
                if "HR Mode" in mode:
                    id_resp = llm.invoke(f"Estrai Nome e Sede dal CV. Rispondi SOLO JSON: {{'nome': '...', 'sede': '...'}}. Testo: {text[:800]}")
                    m_id = re.search(r'\{.*\}', id_resp, re.DOTALL)
                    if m_id:
                        info = json.loads(m_id.group().replace("'", '"'))
                        n_e = info.get('nome', 'Sconosciuto')
                        cur.execute("SELECT id FROM users WHERE nome ILIKE %s", (f"%{n_e}%",))
                        user_ex = cur.fetchone()
                        if user_ex: o_id, o_name = user_ex[0], n_e
                        else:
                            cur.execute("INSERT INTO users (username, password, nome, sede) VALUES (%s, %s, %s, %s) RETURNING id", (n_e.lower().replace(" ","_"), "pass", n_e, info.get('sede','Milano')))
                            o_id, o_name = cur.fetchone()[0], n_e

                f_hash = hashlib.md5(text.encode()).hexdigest()
                cur.execute("INSERT INTO documents (user_id, filename, file_hash) VALUES (%s, %s, %s) RETURNING id", (o_id, f.name, f_hash))
                d_id = cur.fetchone()[0]

                skill_resp = llm.invoke(f"Estrai max 6 skill tecniche (nomi brevi) da: {text[:1000]}. Rispondi SOLO array JSON di stringhe.")
                m_sk = re.search(r'\[.*\]', skill_resp, re.DOTALL)
                skills_list = []
                if m_sk:
                    raw_data = json.loads(m_sk.group().replace("'", '"'))
                    for s in raw_data:
                        s_c = str(s).strip().capitalize()
                        if 2 < len(s_c) < 30:
                            cur.execute("INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (s_c,))
                            cur.execute("SELECT id FROM skills WHERE name=%s", (s_c,))
                            sid = cur.fetchone()[0]
                            cur.execute("INSERT INTO user_skills (user_id, skill_id, doc_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (o_id, sid, d_id))
                            skills_list.append(s_c)
                
                vector_store.add_documents([Document(page_content=text, metadata={"owner_name": o_name, "file_path": f_path})])
                ing_log.append({"file": f.name, "owner": o_name, "skills": skills_list})
            except: pass
        conn.commit(); conn.close()
        st.session_state.last_ing = ing_log
        st.session_state.up_key += 1; st.rerun()

    if 'last_ing' in st.session_state:
        for item in st.session_state.last_ing:
            st.success(f"✅ {item['file']} -> {item['owner']} (Skill: {', '.join(item['skills'])})")

# --- TAB 1: RICERCA (IL CUORE DELLE RISPOSTE PROFESSIONALI) ---
with tab1:
    if 'active_tag' in st.session_state and st.session_state.active_tag:
        st.subheader(f"Dettaglio competenza: {st.session_state.active_tag}")
        conn = get_sql_conn(); cur = conn.cursor()
        cur.execute("SELECT u.nome, u.sede, d.filename FROM users u JOIN user_skills us ON u.id = us.user_id JOIN skills s ON us.skill_id = s.id JOIN documents d ON us.doc_id = d.id WHERE s.name = %s", (st.session_state.active_tag,))
        for row in cur.fetchall():
            st.info(f"👤 **{row[0]}** - {row[1]} (Rif: `{row[2]}`)")
        if st.button("⬅️ Torna alla ricerca"): st.session_state.active_tag = None; st.rerun()
    else:
        query = st.text_input("Descrivi l'esigenza tecnica:")
        if query:
            with st.spinner("L'Agente sta elaborando il report per te..."):
                v_res = vector_store.similarity_search(query, k=5)
                context_list = []
                for d in v_res:
                    context_list.append(f"[DIPENDENTE: {d.metadata.get('owner_name')}] [FILE: {os.path.basename(d.metadata.get('file_path',''))}]\nDESCRIZIONE: {d.page_content[:1000]}")
                context = "\n\n---\n\n".join(context_list)

                prompt = f"""
                Sei un Analista Strategico del Capitale Umano. Rispondi alla domanda del tuo Manager, {u['nome']}.
                
                DOMANDA DEL MANAGER: {query}
                
                CONTESTO AZIENDALE:
                {context}
                
                ISTRUZIONI RIGIDE:
                1. Riferisci i risultati in TERZA PERSONA. Non parlare mai direttamente ai dipendenti trovati.
                2. Non dire "Ciao Luca", stai parlando AL MANAGER.
                3. Per ogni esperto identificato usa questo schema:
                   - **Nome Cognome** (Sede)
                   - Analisi: [Breve spiegazione tecnica della pertinenza]
                   - Documento: [Nome del FILE]
                4. Se non trovi nessuno di pertinente, dillo chiaramente al Manager.
                5. Sii formale, sintetico e professionale. Evita chiacchiere inutili.
                """
                
                placeholder = st.empty(); full_res = ""
                for chunk in llm.stream(prompt):
                    full_res += chunk
                    placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
