import psycopg2
import time

def init():
    print("Tentativo di connessione a Postgres...")
    # Attendiamo che il database sia pronto a ricevere connessioni
    for i in range(15):
        try:
            conn = psycopg2.connect(
                host="localhost", 
                database="knowledge_brain", 
                user="admin", 
                password="password123"
            )
            cur = conn.cursor()
            
            # Creazione Tabella Utenti
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    sede TEXT NOT NULL
                );
            ''')
            
            # Creazione Tabella Documenti (Ownership e Integrità)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    caricato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Inserimento Utenti di Test
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
            print("SUCCESSO: Database PostgreSQL inizializzato con le tabelle 'users' e 'documents'.")
            return
        except Exception as e:
            print(f"Postgres non ancora pronto ({e}). Riprovo tra 2 secondi...")
            time.sleep(2)

if __name__ == "__main__":
    init()
