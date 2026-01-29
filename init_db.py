import psycopg2
import time

def init():
    print("Tentativo di connessione a Postgres...")
    for i in range(15):
        try:
            conn = psycopg2.connect(
                host="localhost", 
                database="knowledge_brain", 
                user="admin", 
                password="password123"
            )
            cur = conn.cursor()
            # Creiamo la tabella users (usata nell'app)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    sede TEXT NOT NULL
                );
            ''')
            # Creiamo la tabella documents
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    caricato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            # Utenti di test
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
            print("DATABASE INIZIALIZZATO: Tabella 'users' pronta.")
            return
        except Exception as e:
            print(f"Postgres non pronto ({e}). Riprovo in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    init()
