import psycopg2

def init_db():
    conn = psycopg2.connect(
        host="localhost",
        database="knowledge_brain",
        user="admin",
        password="password123"
    )
    cur = conn.cursor()
    
    # 1. Tabella Dipendenti (Auth & Profile)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dipendenti (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nome TEXT NOT NULL,
            sede TEXT NOT NULL
        );
    ''')
    
    # 2. Tabella Documenti (Metadata & Ownership)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS documenti (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES dipendenti(id),
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            caricato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Inserimento dati di test (Password in chiaro solo per demo didattica)
    utenti_test = [
        ('mrossi', 'web123', 'Marco Rossi', 'Milano'),
        ('lbianchi', 'back123', 'Luca Bianchi', 'Milano'),
        ('rwilson', 'cloud123', 'Robert Wilson', 'New York'),
        ('saminah', 'ai123', 'Siti Aminah', 'Singapore')
    ]
    
    for u in utenti_test:
        cur.execute("INSERT INTO dipendenti (username, password, nome, sede) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", u)

    conn.commit()
    cur.close()
    conn.close()
    print("Database SQL (PostgreSQL) inizializzato con successo.")

if __name__ == "__main__":
    init_db()
