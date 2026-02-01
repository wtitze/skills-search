import psycopg2
import json
import os
from pypdf import PdfReader
from langchain_ollama import OllamaLLM

# --- CONFIGURAZIONI ---
UPLOAD_DIR = "uploads"

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

# Inizializziamo l'LLM per l'estrazione
llm = OllamaLLM(model="llama3.1:8b", temperature=0)

def extract_skills(text):
    prompt = f"""
    Analizza il seguente testo ed estrai una lista JSON delle competenze tecniche, 
    linguaggi, strumenti o certificazioni menzionati.
    Rispondi SOLO con il JSON, esempio: ["Java", "SQL", "Cloud Security"].
    
    TESTO:
    {text[:2000]}
    """
    try:
        response = llm.invoke(prompt)
        start = response.find("[")
        end = response.rfind("]") + 1
        return json.loads(response[start:end])
    except:
        return []

def run_migration():
    conn = get_sql_conn()
    cur = conn.cursor()

    # 1. Recuperiamo tutti i documenti che non hanno ancora skill associate
    cur.execute('''
        SELECT d.id, d.user_id, d.filename 
        FROM documents d
        LEFT JOIN user_skills us ON d.id = us.doc_id
        WHERE us.doc_id IS NULL
    ''')
    docs_to_process = cur.fetchall()

    if not docs_to_process:
        print("✅ Tutti i documenti sono già allineati con i Tag SQL.")
        return

    print(f"🔄 Trovati {len(docs_to_process)} documenti da analizzare...")

    for doc_id, user_id, filename in docs_to_process:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            print(f"⚠️ File non trovato: {file_path}")
            continue

        print(f"[*] Analisi di {filename}...")
        
        # Lettura file
        text = ""
        try:
            if filename.endswith('.pdf'):
                reader = PdfReader(file_path)
                for page in reader.pages: text += page.extract_text()
            else:
                with open(file_path, "r", encoding="utf-8") as f: text = f.read()
        except Exception as e:
            print(f"❌ Errore lettura {filename}: {e}")
            continue

        # Estrazione e Sincronizzazione
        skills = extract_skills(text)
        for s in skills:
            s_clean = s.strip().capitalize()
            # Inserisce la skill nel dizionario se manca
            cur.execute("INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (s_clean,))
            cur.execute("SELECT id FROM skills WHERE name = %s", (s_clean,))
            skill_id = cur.fetchone()[0]
            # Collega l'utente alla skill
            cur.execute("INSERT INTO user_skills (user_id, skill_id, doc_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                       (user_id, skill_id, doc_id))
        
        print(f"   -> Estratte {len(skills)} competenze per {filename}")
        conn.commit()

    cur.close()
    conn.close()
    print("✨ Migrazione completata con successo!")

if __name__ == "__main__":
    run_migration()
