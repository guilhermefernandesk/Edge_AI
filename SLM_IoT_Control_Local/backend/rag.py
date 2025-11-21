'''
Install:
pip install -U 'langchain-chroma'
pip install -U langchain
pip install -U langchain-community
pip install -U langchain-ollama
pip install -U langchain-text-splitter
pip install -U langchain-community pypdf
pip install tiktoken

- pip install -U langsmith
'''

import os
import time
import requests
import concurrent.futures
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma
# from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings


# from langsmith import Client  # updated SDK
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# import warnings

# Suppress LangSmith warnings
# warnings.filterwarnings("ignore", 
#                         message="API key must be provided when using hosted LangSmith API",
#                         category=UserWarning)

# ollama pull all-minilm;
# ollama pull gemma3;

class RAG:
    def __init__(
        self, 
        persist_dir, 
        model, 
        urls, 
        pdfs,
        text,   
        embed_model="nomic-embed-text",
        collection_name="rag_collection",
        chunk_size=300,
        chunk_overlap=30
    ):
        self.persist_dir = persist_dir
        self.model = model
        self.urls = urls
        self.pdfs = pdfs
        self.text = text
        self.embed_model = embed_model
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vectorstore = None
        self.retriever = None

        # self.llm = ChatOllama(model=self.model, temperature=0)

        self.preload_models()
        self.create_vectorstore(self.urls, self.pdfs, self.text, recreate=False)
        self.load_vectorstore()

    # --------------------------------------------------------
    # Custom embedding class that uses Ollama directly and implements caching
    # --------------------------------------------------------
    class OptimizedOllamaEmbeddings:
        def __init__(self, embed_model):
            self.embed_model = embed_model

        # Direct Ollama API functions for better performance
        def direct_ollama_embed(self, text):
            """Get embeddings directly from Ollama API"""
            response = requests.post(
                "http://ollama:11434/api/embeddings",
                json={"model": self.embed_model, "prompt": text}
            )
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                raise Exception(f"Error from Ollama API: {response.status_code}")

        # Cache embeddings to avoid recalculating
        @lru_cache(maxsize=100)
        def cached_embed_query(self, text):
            """Cache embeddings for repeated queries"""
            return self.direct_ollama_embed(text)

        def embed_query(self, text):
            """Get embeddings for a query with caching"""
            return self.cached_embed_query(text)
        
        def embed_documents(self, documents):
            """Get embeddings for documents - not cached as this is mainly used during DB creation"""
            results = []
            # Process in batches of 4 for efficiency
            batch_size = 4
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    batch_results = list(executor.map(self.direct_ollama_embed, batch))
                results.extend(batch_results)
            return results

    # --------------------------------------------------------
    # Model warm-up
    # --------------------------------------------------------
    def preload_models(self):
        print("[INFO] Preloading Ollama models...")
        try:
            # Warm embedding model
            requests.post(
                "http://ollama:11434/api/embeddings",
                json={"model": self.embed_model, "prompt": "warmup"},
                timeout=30
            )

            # Warm LLM
            requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": "warmup",
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30
            )
            print("[INFO] Models ready!")
        except Exception as e:
            print(f"Warning: Model preloading failed: {e}")
            print("Continuing anyway - first query may be slower")
    
    # --------------------------------------------------------
    # Vectorstore creation
    # --------------------------------------------------------
    def create_vectorstore(self, urls=None, pdfs=None, text=None, recreate=False):
        """Creates the Chroma DB from scratch."""

        # Check if database already exists
        if os.path.exists(self.persist_dir):
            print(f"[INFO] Database already exists at {self.persist_dir}.")
            if not recreate:
                print("[INFO] Skipping database creation.")
                return
            else:
                print("[INFO] Recreating database...")

        # Load documents
        print("[INFO] Loading documents...")

        # PDFs
        docs_list = []
        for pdf in pdfs:
            if os.path.exists(pdf):
                print(f"Loading PDF: {pdf}")
                loader = PyPDFLoader(pdf)
                docs_list.extend(loader.load())
            else:
                print(f"Warning: PDF file {pdf} not found")

        # URLs
        for url in urls:
            try:
                web_docs = []
                print(f"Loading URL: {url}")
                loader = WebBaseLoader(url)
                web_docs.extend(loader.load())
                docs_list.extend(web_docs)
            except Exception as e:
                print(f"Error loading URL documents: {e}")

        # Plain text
        for txt in text:
            docs_list.append({"page_content": txt})

        if not docs_list:
            print("Error: No documents were loaded. Check file paths, URLs and Text.")
            return None

        print(f"[INFO] {len(docs_list)} documents loaded.")
        
        # Split documents
        print("Splitting documents into chunks...")
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        chunks = splitter.split_documents(docs_list)
        print(f"[INFO] {len(chunks)} chunks created.")

        # Create embedding function
        print("Initializing embedding model...")
        embedding_function = OllamaEmbeddings(model=self.embed_model)

        # Create and persist vectorstore to disk
        print("Creating vector database...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            collection_name=self.collection_name,
            embedding=embedding_function,
            persist_directory=self.persist_dir,
        )

        # Important: persist to disk
        # self.vectorstore.persist()

        print(f"Total documentos carregados: {len(docs_list)}")
        print(f"[SUCCESS] Vector DB saved at {self.persist_dir}")

    # --------------------------------------------------------
    # Load existing vectorstore
    # --------------------------------------------------------
    def load_vectorstore(self):
        """Load the vector store from disk and create an optimized retriever"""
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError("Vectorstore not found. Run create_vectorstore() first.")

        print("Loading existing vector store...")

        embedding_function = self.OptimizedOllamaEmbeddings(self.embed_model)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedding_function,
            persist_directory=self.persist_dir,
        )

        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",  # Basic similarity is fastest
            search_kwargs={"k": 2} # Retrieve fewer documents
        )

        print("[INFO] Vectorstore loaded.")

    # --------------------------------------------------------
    # Query RAG
    # --------------------------------------------------------
    def query(self, question):
        """Generate an answer using the RAG system with optimized processing"""
        if not self.retriever:
            raise RuntimeError("Retriever not initialized. Call load_vectorstore().")
        
        # Start timing
        start_time = time.time()
        
        # Retrieve relevant documents
        print(f"Question: {question}")
        print("Retrieving documents...")
        docs = self.retriever.invoke(question)
        
        # Early check if we found any relevant documents
        if not docs:
            end_time = time.time()
            latency = end_time - start_time
            print(f"No relevant documents found. Response latency: {latency:.2f} seconds")
            return "I don't have enough information to answer this question accurately."
        
        # Process documents - extract only what we need
        docs_content = "\n\n".join(doc.page_content for doc in docs)
        print(f"Retrieved {len(docs)} document chunks")
        
        # Generate answer
        print("Generating answer...")

        # Using new LangSmith client and pull_prompt
        # client = Client()
        # rag_prompt = client.pull_prompt("rlm/rag-prompt")

        # Compose the RAG chain
        # if isinstance(rag_prompt, str):
            # rag_prompt = ChatPromptTemplate.from_template(rag_prompt)

        # rag_chain = rag_prompt | self.llm | StrOutputParser()
        # answer = rag_chain.invoke({"context": docs_content, "question": question})
        
        # Simplified RAG prompt for efficiency
        rag_prompt = f"""
            You are an AI assistant specialized in Franzininho documentation.
            Answer the following question based only on the information provided in the context below.
            Be concise and direct. If the context doesn't contain relevant information, admit that you don't know.

            Context:
            {docs_content}

            Question: {question}

            Answer:
        """

        """Generate response directly from Ollama API"""
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": self.model,
                "prompt": rag_prompt,
                "stream": False,
                "options": {
                    "num_predict": 512,
                    "temperature": 0,
                    "top_k": 40,
                    "top_p": 0.9,
                    "seed": 42  # Fixed seed for consistent outputs
                }
            }
        )
        print(response.json()["response"])
        if response.status_code == 200:
            answer = response.json()["response"]
        else:
            answer = f"Error: Received status code {response.status_code} from Ollama API"
        
        # Calculate and print latency
        end_time = time.time()
        latency = end_time - start_time
        print(f"Response latency: {latency:.2f} seconds using model: {self.model}")
        
        return answer