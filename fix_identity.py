import psycopg2
import json
import os
from pypdf import PdfReader
from langchain_ollama import OllamaLLM

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

llm = OllamaLLM(model="llama3.1:8b", temperature=0)

def extract_identity_and_skills(text):
    prompt = f"""
    Analizza il seguente CV ed estrai:
    1. Il NOME COMPLETO della persona a cui appartiene il CV.
    2. Una lista delle sue COMPETENZE tecniche.
    
    Rispondi SOLO con un JSON così strutturato:
    {{"nome": "Nome Cognome", "skills": ["Skill1", "Skill2"]}}
    
    TESTO:
    {text[:2000]}
    """
    try:
        response = llm.invoke(prompt)
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except:
        return None

def run_repair():
    conn = get_sql_conn()
    cur = conn.cursor()

    # 1. Puliamo la tabella delle relazioni errate
    print("🧹 Pulizia relazioni competenze errate...")
    cur.execute("DELETE FROM user_skills;")
    conn.commit()

    # 2. Recuperiamo tutti i documenti caricati
    cur.execute("SELECT id, filename FROM documents")
    docs = cur.fetchall()

    for doc_id, filename in docs:
        file_path = os.path.join("uploads", filename)
        if not os.path.exists(file_path): continue

        print(f"[*] Riconciliazione di {filename}...")
        
        # Lettura
        text = ""
        if filename.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages: text += page.extract_text()
        else:
            with open(file_path, "r", encoding="utf-8") as f: text = f.read()

        # Estrazione Identità e Skill
        data = extract_identity_and_skills(text)
        if not data: continue

        real_name = data.get("nome")
        skills = data.get("skills", [])

        # 3. Cerchiamo se l'utente esiste già nel DB SQL
        # Cerchiamo per similitudine nel nome
        cur.execute("SELECT id FROM users WHERE nome ILIKE %s", (f"%{real_name}%",))
        user_res = cur.fetchone()

        if user_res:
            correct_user_id = user_res[0]
            print(f"   -> Assegnazione a: {real_name} (ID: {correct_user_id})")
            
            for s in skills:
                s_clean = s.strip().capitalize()
                cur.execute("INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (s_clean,))
                cur.execute("SELECT id FROM skills WHERE name = %s", (s_clean,))
                skill_id = cur.fetchone()[0]
                cur.execute("INSERT INTO user_skills (user_id, skill_id, doc_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                           (correct_user_id, skill_id, doc_id))
        else:
            print(f"   ⚠️ Utente '{real_name}' non trovato in anagrafica SQL. Skill non associate.")
        
        conn.commit()

    cur.close()
    conn.close()
    print("✨ Riconciliazione completata!")

if __name__ == "__main__":
    run_repair()
