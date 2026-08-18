import os
import sys
import re
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load Environment Variables from .env file
load_dotenv()

# Check for GROQ_API_KEY in environment
if not os.getenv("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not found. Please set it in your .env file.")
    sys.exit(1)

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# CONFIGURATION
DATA_PATH = "./UNIVERSITY"  # Folder where your .txt files are
DB_PATH = "./faiss_index"     # Folder to save the vector database

# University keyword mapping - maps keywords in user query to folder names
UNIVERSITY_KEYWORDS = {
    # SMIU variations
    "smiu": "smiu",
    "sindh madressatul islam": "smiu",
    "sindh madressatul": "smiu",
    "madressatul islam": "smiu",
    "smi university": "smiu",
    
    # NED variations
    "ned": "ned",
    "ned university": "ned",
    "ned karachi": "ned",
    "neduet": "ned",

    # DUET variations
    "duet": "duet",
    "dawood university": "duet",
    "dawood engineering": "duet",

    # UOK variations
    "uok": "uok",
    "ku": "uok",
    "karachi university": "uok",
    "university of karachi": "uok",
    
    # DSU variations
    "dsu": "dsu",
    "dha suffa": "dsu",
    "dha suffa university": "dsu",
    "suffa university": "dsu",
    
    # IBA variations
    "iba": "iba",
    "iba karachi": "iba",
    "institute of business administration": "iba",
    "business administration": "iba",
    
    # Szabist variations
    "szabist": "szabist",
    "szabist karachi": "szabist",
    "shaheed zulfikar ali bhutto": "szabist",
    "zulfikar ali bhutto institute": "szabist",

    # FAST variations
    "fast": "fast",
    "fast nuces": "fast",
    "nuces": "fast",
    "fast university": "fast",
    "national university of computer": "fast",
}

# Cached singletons for high performance
_cached_embeddings = None
_cached_db = None
_cached_llm = None

def get_embeddings():
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return _cached_embeddings

def get_vector_db():
    global _cached_db
    if _cached_db is None:
        if not os.path.exists(DB_PATH):
            create_vector_db()
        _cached_db = FAISS.load_local(DB_PATH, get_embeddings(), allow_dangerous_deserialization=True)
    return _cached_db

def get_llm():
    global _cached_llm
    if _cached_llm is None:
        _cached_llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.05,
            max_tokens=3000
        )
    return _cached_llm

def detect_university(query):
    """
    Detects university name from user query using keyword matching.
    Returns the university folder name (lowercase) or None if not detected.
    """
    query_lower = query.lower()
    for keyword, uni_name in UNIVERSITY_KEYWORDS.items():
        if keyword in query_lower:
            return uni_name
    return None

def create_vector_db():
    """
    Reads .txt files, creates embeddings using HuggingFace model,
    and saves them to a local Faiss database.
    """
    global _cached_db
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"[!] Created folder {DATA_PATH}. Please put your .txt files there and run again!")
        return False

    print("--- INGESTION STARTED ---")
    
    # 1. Load Documents 
    print("1. Loading documents...")
    documents = []

    for root, dirs, files in os.walk(DATA_PATH):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                university = os.path.basename(root).lower()

                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()

                for doc in docs:
                    doc.metadata["university"] = university
                    doc.metadata["source_file"] = file
                    documents.append(doc)

    if not documents:
        print("[X] No documents found. Add .txt files to UNIVERSITY folders.")
        return False
        
    print(f"   Loaded {len(documents)} documents.")

    # 2. Split Text
    print("2. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, 
        chunk_overlap=350,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   Created {len(chunks)} chunks.")

    # 3. Create Embeddings
    print("3. Creating Embeddings...")
    embeddings = get_embeddings()

    # 4. Save to FAISS
    print("4. Saving to Vector DB...")
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(DB_PATH)
    _cached_db = db
    print("--- INGESTION COMPLETE ---")
    return True

def get_groq_response(query):
    """
    Retrieves context from DB and sends it to Groq LLM with optimized prompting.
    """
    clean_query = query.strip()
    # Strip potential prefix like "SMIU: " if passed from UI dropdown
    search_query = re.sub(r'^(smiu|ned|iba|uok|fast|szabist|dsu|duet):\s*', '', clean_query, flags=re.IGNORECASE).strip()
    if not search_query:
        search_query = clean_query

    detected_university = detect_university(clean_query)
    db = get_vector_db()
    llm = get_llm()

    docs = []
    if detected_university:
        try:
            print(f"   [Filtering by university: {detected_university.upper()}]")
            retriever = db.as_retriever(
                search_kwargs={
                    "k": 5,
                    "filter": {"university": detected_university}
                }
            )
            docs = retriever.invoke(search_query)
        except Exception as e:
            print(f"Filtered retrieval error: {e}")
            docs = []
            
    if not docs:
        retriever = db.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(search_query)

    context = "\n\n".join([d.page_content for d in docs])

    template = """You are a helpful university assistant specifically designed to help students with their academic queries. Your goal is to provide clear, concise, accurate, and student-friendly responses based on the provided context and general knowledge of the universities.

Context from university documents:
{context}

Student Question: {question}

Instructions for your response:
1. Answer the question directly, concisely, and accurately.
2. Keep your answer brief and suitable for mobile screens and voice readout.
3. DO NOT use hyphens or dashes ('-') or asterisks ('*') or hash symbols ('##') in your text response.
4. If listing items, use plain line breaks or numbered lists (1., 2., 3.).
5. If the context does not fully answer the question, briefly provide what is available and suggest contacting the relevant university department.
6. Do not include thinking or internal reasoning blocks, output only the clean final answer.

Your Answer:"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = (
        {"context": lambda _: context, "question": lambda _: search_query}
        | prompt
        | llm
        | StrOutputParser()
    )

    response = chain.invoke(search_query)

    # Clean thinking tags manually
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<think>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<thought>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Normalize unicode special spaces, quotes, hyphens
    response = response.replace('\u202f', ' ').replace('\u00a0', ' ')
    response = response.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', ' ')
    response = response.replace('\u2018', "'").replace('\u2019', "'")
    response = response.replace('\u201c', '"').replace('\u201d', '"')
    response = response.replace('**', '')

    # Split into lines to clean line-start bullets safely
    lines = response.splitlines()
    cleaned_lines = []
    for line in lines:
        sline = line.strip()
        if sline.startswith('- '):
            sline = sline[2:]
        elif sline.startswith('-'):
            sline = sline[1:]
        if sline:
            cleaned_lines.append(sline)
        
    response = "\n".join(cleaned_lines).strip()
    return response

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Creating it now...")
        success = create_vector_db()
        if not success:
            sys.exit()
    
    print("\n[OK] System Ready! Ask me anything about your university.")
    print("Tip: Be specific in your questions for the best answers!")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye! Good luck with your studies!")
            break
            
        if user_input.lower() == "/rebuild":
            print("\nRebuilding database...")
            create_vector_db()
            print("Database rebuilt successfully!\n")
            continue
        
        if not user_input.strip():
            continue
            
        print("\nAssistant: ", end="")
        answer = get_groq_response(user_input)
        print(answer)