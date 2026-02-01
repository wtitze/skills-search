import psycopg2
import json
import os
import hashlib
from pypdf import PdfReader
from langchain_ollama import OllamaLLM

def get_sql_conn():
    return psycopg2.connect(host="localhost", database="knowledge_brain", user="admin", password="password123")

llm = OllamaLLM(model="llama3.1:8b", temperature=0)

def analyze_document_comprehensive(text, filename):
    prompt = f"""
    Analizza questo documento aziendale ({filename}).
    
    1. Determina se è un CV (Curriculum Vitae) o un DOCUMENTO TECNICO (Paper/Slide).
    2. Se è un CV, estrai NOME COMPLETO e SEDE (Milano, Singapore, New York).
    3. Estrai una lista di COMPETENZE tecniche menzionate.
    
    Rispondi SOLO con un JSON:
    {{
      "tipo": "CV" o "TECNICO",
      "nome": "Nome Cognome" (o null se tecnico),
      "sede": "Sede" (o null se tecnico),
      "skills": ["Skill1", "Skill2"]
    }}
    
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

def run_consolidation():
    conn = get_sql_conn()
    cur = conn.cursor()

    print("🧹 Reset tabelle competenze per consolidamento totale...")
    cur.execute("DELETE FROM user_skills;")
    conn.commit()

    cur.execute("SELECT id, user_id, filename FROM documents")
    docs = cur.fetchall()

    for doc_id, uploader_id, filename in docs:
        file_path = os.path.join("uploads", filename)
        if not os.path.exists(file_path): continue

        print(f"[*] Analisi profonda di {filename}...")
        
        text = ""
        if filename.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages: text += page.extract_text()
        else:
            with open(file_path, "r", encoding="utf-8") as f: text = f.read()

        data = analyze_document_comprehensive(text, filename)
        if not data: continue

        # LOGICA DI ASSEGNAZIONE IDENTITÀ
        final_user_id = None
        
        if data.get("tipo") == "CV" and data.get("nome"):
            # Caso CV: cerchiamo o creiamo il dipendente
            nome = data["nome"]
            sede = data.get("sede") or "Non specificata"
            cur.execute("SELECT id FROM users WHERE nome ILIKE %s", (f"%{nome}%",))
            user_res = cur.fetchone()
            
            if user_res:
                final_user_id = user_res[0]
            else:
                # AUTO-ENROLLMENT: Creiamo il nuovo utente
                username = nome.lower().replace(" ", "")
                print(f"   👤 Nuovo dipendente rilevato: {nome}. Creazione account...")
                cur.execute("INSERT INTO users (username, password, nome, sede) VALUES (%s, %s, %s, %s) RETURNING id", 
                           (username, 'password_provvisoria', nome, sede))
                final_user_id = cur.fetchone()[0]
        else:
            # Caso Documento Tecnico: assegniamo a chi ha fatto l'upload
            final_user_id = uploader_id
            print(f"   📄 Documento tecnico rilevato. Assegnazione all'uploader (ID: {uploader_id})")

        # INSERIMENTO SKILLS
        if final_user_id:
            for s in data.get("skills", []):
                s_clean = s.strip().capitalize()
                cur.execute("INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (s_clean,))
                cur.execute("SELECT id FROM skills WHERE name = %s", (s_clean,))
                skill_id = cur.fetchone()[0]
                cur.execute("INSERT INTO user_skills (user_id, skill_id, doc_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                           (final_user_id, skill_id, doc_id))
        
        conn.commit()

    cur.close()
    conn.close()
    print("\n✨ DATABASE CONSOLIDATO E ALLINEATO!")

if __name__ == "__main__":
    run_consolidation()
