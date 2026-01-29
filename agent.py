import sys
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 agent.py 'tua domanda'")
        return

    user_query = " ".join(sys.argv[1:])
    
    # 1. SETUP
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = OllamaLLM(model="llama3.2")
    client = QdrantClient(url="http://localhost:6333")
    vector_store = QdrantVectorStore(client=client, collection_name="knowledge_brain", embedding=embeddings)

    print(f"[*] Fase 1: Pianificazione e Analisi della query...")
    
    # 2. AGENTIC STEP: QUERY EXPANSION (Cap 6.5)
    # Chiediamo all'IA di espandere i termini tecnici per aiutare il database
    expansion_prompt = f"""
    Analizza questa richiesta di ricerca personale: '{user_query}'
    Elenca 5 termini tecnici o brand correlati che potrebbero apparire in un CV.
    Esempio: se cerchi 'Microsoft', includi 'Azure'. Se cerchi 'Frontend', includi 'React, Angular'.
    Rispondi SOLO con i termini separati da virgola.
    """
    expanded_terms = llm.invoke(expansion_prompt)
    search_query = f"{user_query}, {expanded_terms}"
    print(f"[*] Query espansa per il database: {search_query}")

    # 3. RETRIEVAL (Cap 6.4)
    # Aumentiamo k=5 per dare più scelta all'agente nella fase di riflessione
    related_docs = vector_store.similarity_search(search_query, k=5)
    
    context = ""
    for i, doc in enumerate(related_docs):
        context += f"\n--- CANDIDATO {i+1} ---\n{doc.page_content}\n"

    # 4. AGENTIC STEP: REFLECTION & REASONING (Cap 6.7)
    final_prompt = f"""
    Sei un Agente HR esperto in informatica. 
    Analizza i seguenti candidati estratti dal database aziendale.
    
    COMPITO:
    Rispondi alla domanda dell'utente: '{user_query}'
    
    CANDIDATI DISPONIBILI:
    {context}

    ISTRUZIONI CRITICHE:
    1. RAGIONA: Se cerchi sviluppo web, dai priorità a chi usa React/Node/HTML, non Android/iOS.
    2. BRAND: Azure è un prodotto Microsoft. Se cerchi Microsoft, Robert Wilson è il tuo uomo.
    3. SELEZIONE: Seleziona solo i profili DAVVERO pertinenti. Se un profilo non c'entra, ignoralo.
    4. SINTESI: Presenta Nome, Sede e il MOTIVO tecnico per cui è perfetto.

    RISPOSTA DELL'AGENTE:
    """

    print("\n=== RISPOSTA AGENTICA FINALE (Streaming) ===")
    try:
        for chunk in llm.stream(final_prompt):
            print(chunk, end="", flush=True)
        print("\n\n=== FINE RICERCA ===")
    except Exception as e:
        print(f"\nErrore: {e}")

if __name__ == "__main__":
    main()
