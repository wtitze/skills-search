import os
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# 1. Configurazione: usiamo un modello di embedding locale (leggero per Codespaces)
# In produzione useremmo modelli più pesanti sulla GPU dedicata.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Caricamento dei file dalla cartella /pdf
documents = []
for file in os.listdir("pdf"):
    if file.endswith(".txt"):
        loader = TextLoader(os.path.join("pdf", file))
        documents.extend(loader.load())

# 3. Chunking: Dividiamo i CV in parti significative (AI Engineering Principles)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# 4. Caricamento nel Vector Database (Long-term Memory)
url = "http://localhost:6333"
collection_name = "knowledge_brain"

qdrant = QdrantVectorStore.from_documents(
    docs,
    embeddings,
    url=url,
    collection_name=collection_name,
)

print(f"Successo! Indicizzati {len(docs)} frammenti di conoscenza da {len(documents)} CV.")
