# Knowledge Brain: Sistema Agentico di Gestione delle Competenze

## 1. Visione del Progetto
Questa piattaforma nasce per risolvere il problema del **"Sapere Nascosto"** all'interno di società di ricerca globali. Troppo spesso l'azienda paga consulenti esterni per competenze che già possiede internamente, ma che sono invisibili perché frammentate tra i vari centri di ricerca o sepolte in documenti non strutturati (CV, slide di corsi, certificazioni).

### Obiettivi Chiave:
- **Zero Data-Entry:** Il dipendente non compila form. Carica semplicemente i documenti che testimoniano la sua crescita (CV aggiornati, slide di corsi seguiti, paper).
- **Ricerca Intelligente (Agentica):** Il sistema non cerca solo parole chiave, ma "comprende" il bisogno del manager e trova esperti in settori affini.
- **Privacy Totale:** Sistema installato **On-Premise** (sui server aziendali). Nessun dato esce dai confini societari.

---

## 2. Architettura del Sistema (AI Engineering - Cap. 6)
Il sistema segue l'approccio **Agentic RAG**, trasformando l'Intelligenza Artificiale da semplice motore di ricerca a un **Agente attivo** che pianifica e riflette.

### Componenti Principali:
1.  **Agente (Planner & Evaluator):** 
    - Il **Planner** scompone la richiesta dell'utente in sotto-task logici.
    - L'**Evaluator** applica la *Reflection*: controlla se i risultati trovati sono realmente pertinenti prima di mostrarli. Se non lo sono, corregge il piano di ricerca.
2.  **Tool Inventory (Strumenti):**
    - **Text Retriever:** Cerca nei contenuti semantici (esperienze descritte nei CV, concetti nelle slide).
    - **SQL Executor:** Accede ai dati strutturati (sede del dipendente, ore di formazione, disponibilità).
    - **Query Rewriter:** Ottimizza le domande ambigue per renderle più efficaci nel database.
3.  **Memoria Multilivello:**
    - **Long-term (Vector DB):** Dove risiede tutta la conoscenza estratta dai documenti caricati.
    - **Short-term (Context):** Ricorda i passi della conversazione attuale per affinare la ricerca.

---

## 3. Flusso Operativo in 5 Passi
1.  **Input:** Caricamento file (PDF, PPTX, DOCX) senza compilazione di moduli.
2.  **Analisi:** L'IA estrae automaticamente competenze, date e livelli di expertise.
3.  **Indicizzazione:** Il sapere viene convertito in "vettori di significato" nella Biblioteca Digitale.
4.  **Ricerca:** Il manager interroga il sistema in linguaggio naturale (es. *"Chi può aiutarmi con un problema di corrosione a Singapore?"*).
5.  **Matching:** L'Agente propone i profili migliori, spiegando il motivo della scelta e citando i documenti di origine.

---

## 4. Requisiti Tecnici (On-Premise)

### Software (Open Source)
- **S.O.:** Linux Ubuntu Server + Docker.
- **Modello IA:** Llama 3 / Mistral (Esecuzione locale tramite vLLM o Ollama).
- **Database:** Qdrant (Vettoriale) e PostgreSQL (Relazionale).
- **Orchestratore:** LangGraph / LangChain.

### Hardware Consigliato
- **GPU:** NVIDIA RTX 4090 o A100 (fondamentale per il "ragionamento" dell'agente).
- **RAM:** 64GB - 128GB.
- **Storage:** SSD NVMe 1TB+ per accesso rapido ai documenti.

---

## 5. Roadmap di Sviluppo (10 Settimane)
- **Settimane 1-2:** Setup Infrastruttura Hardware e installazione LLM locale.
- **Settimane 3-6:** Sviluppo motore di analisi (Ingestion) e Tool Inventory.
- **Settimane 4-7:** Sviluppo Portale di Ricerca (UI) - *Attività in parallelo*.
- **Settimane 8-10:** Fase di Test (Reflection Tuning), Raffinamento e Training utenti.

---
*Progetto realizzato seguendo i principi di AI Engineering per la massima valorizzazione del capitale umano.*
