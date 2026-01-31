# 🧠 Knowledge Brain: Enterprise Agentic Skill Search

## 🚀 Visione del Progetto
**Knowledge Brain** è una piattaforma di Knowledge Management progettata per società di ricerca globali. Il sistema elimina il problema delle "competenze invisibili", mappando in tempo reale le abilità dei dipendenti senza richiedere data-entry manuale.

L'applicazione segue i principi di **AI Engineering** (Chip Huyen) e implementa un'architettura **Agentic RAG** (basata sul Capitolo 6 degli Agenti), garantendo che ogni informazione sia tracciabile, verificata e mantenuta al 100% all'interno del perimetro aziendale (**On-Premise**).

## ✨ Caratteristiche Principali
- **Zero Data-Entry:** I dipendenti caricano semplicemente documenti in formato PDF o TXT (CV, slide, paper). L'IA estrae e indicizza la conoscenza automaticamente.
- **Identità Ibrida:** Il sistema riconosce la proprietà del dato tramite la sessione di Login (per documenti personali) o tramite analisi del testo (per caricamenti massivi di CV in modalità HR).
- **Agente HR Intelligente:** Utilizza **Llama 3.1 8B** su GPU locale per espandere le query, riflettere sulla pertinenza tecnica e fornire risposte professionali sintetizzate senza "allucinazioni".
- **Tracciabilità delle Fonti:** Ogni risposta cita obbligatoriamente il percorso del file originale (`file_path`) come prova documentale.
- **Performance Locale:** Sfrutta la potenza delle GPU NVIDIA (RTX 3060+) per risposte istantanee in streaming.

## 🏗️ Architettura del Sistema
Il sistema si basa su un **"Triangolo della Memoria"** per massimizzare velocità e coerenza:
1.  **PostgreSQL (SQL):** Memoria strutturata per anagrafica utenti e integrità dei file (MD5 Hash).
2.  **Qdrant (Vector DB):** Memoria semantica per la ricerca concettuale tramite modelli di Embedding (*all-MiniLM-L6-v2*).
3.  **Redis (Cache/History):** Memoria di lavoro per la cronologia delle ricerche e la gestione delle sessioni.

## 🛠️ Requisiti e Installazione (Notebook Locale)

### Prerequisiti
- **Windows 11** con Docker Desktop (WSL2 attivo).
- **Ollama** installato con modello ```llama3.1:8b```.
- **GPU NVIDIA** (Driver v550+).
- **Python 3.10+**.

### Configurazione Iniziale
1. **Avvio Database (Docker):**
   ```bash
   docker compose up -d
   ```

2. **Setup Ambiente Python:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install streamlit psycopg2-binary redis qdrant-client langchain-qdrant langchain-huggingface langchain-ollama sentence-transformers pypdf fpdf2
   ```

3. **Inizializzazione Database SQL:**
   ```bash
   python init_db.py
   ```

4. **Lancio Applicazione:**
   ```bash
   streamlit run app.py
   ```

## 📂 Struttura della Repository
- `app.py`: Core dell'applicazione (Interfaccia, Orchestrazione Agente).
- `init_db.py`: Script di configurazione utenti di test.
- `docker-compose.yml`: Definizione container (Postgres, Qdrant, Redis).
- `uploads/`: Archivio fisico dei documenti caricati.
- `architettura_*.svg`: Schemi tecnici del sistema.

## 🛡️ Sicurezza e Riservatezza
Il sistema è **On-Premise per design**. Tutte le elaborazioni (OCR, Vettorizzazione, Ragionamento LLM) avvengono localmente. Nessun dato viene inviato a cloud esterni, garantendo la protezione assoluta del segreto industriale.

---
*Sviluppato secondo i canoni del moderno AI System Design.*
