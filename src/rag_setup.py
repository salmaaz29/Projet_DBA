from src.helper import load_pdf, text_split, download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os

# Load env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "oracle"
REGION = "us-east-1"

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found")

# Load & process docs
extracted_data = load_pdf("data/")
text_chunks = text_split(extracted_data)
embeddings = download_hugging_face_embeddings()

# Init Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create namespaces 
existing_indexes = [i["name"] for i in pc.list_indexes()]

if INDEX_NAME not in existing_indexes:
    print(f"[INFO] Creating index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=REGION
        )
    )
else:
    print(f"[INFO] Index '{INDEX_NAME}' already exists")

# Create vector store (LangChain)
vectorstore = PineconeVectorStore.from_documents(
    documents=text_chunks,
    embedding=embeddings,
    index_name=INDEX_NAME
)

print(" Documents successfully indexed into Pinecone")