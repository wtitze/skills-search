import psycopg2
import time

def init_db():
    print("Connessione a PostgreSQL per configurazione schema v7.0...")
    for i in range(10):
        try:
            conn = psycopg2.connect(
                host="localhost", 
                database="knowledge_brain", 
                user="admin", 
                password="password123"
            )
            cur = conn.cursor()
            
            # 1. Tabella Utenti
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    sede TEXT NOT NULL
                );
            ''')
            
            # 2. Tabella Documenti
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    caricato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # 3. Tabella Skills (Il dizionario dei Tag)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                );
            ''')

            # 4. Tabella User_Skills (Il legame certo estratto dall'IA)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_skills (
                    user_id INTEGER REFERENCES users(id),
                    skill_id INTEGER REFERENCES skills(id),
                    doc_id INTEGER REFERENCES documents(id),
                    PRIMARY KEY (user_id, skill_id, doc_id)
                );
            ''')
            
            # Inserimento utenti di test
            utenti = [
                ('mrossi', 'password', 'Marco Rossi', 'Milano'),
                ('srusso', 'password', 'Sofia Russo', 'Milano'),
                ('saminah', 'password', 'Siti Aminah', 'Singapore'),
                ('rwilson', 'password', 'Robert Wilson', 'New York')
            ]
            for u in utenti:
                cur.execute("INSERT INTO users (username, password, nome, sede) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", u)
            
            conn.commit()
            cur.close()
            conn.close()
            print("SUCCESSO: Schema SQL Ibrido configurato correttamente.")
            return
        except Exception as e:
            print(f"Errore: {e}. Riprovo...")
            time.sleep(2)

if __name__ == "__main__":
    init_db()
