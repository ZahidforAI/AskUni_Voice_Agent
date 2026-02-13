import os
import sys
import re
from dotenv import load_dotenv

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
    Reads .txt files, creates embeddings using a FREE HuggingFace model,
    and saves them to a local Faiss database.
    """
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

            # Extract university name from folder
            university = os.path.basename(root).lower()

            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()

            for doc in docs:
                doc.metadata["university"] = university
                doc.metadata["source_file"] = file
                documents.append(doc)

    if not documents:
        print("[X] No documents found. Add .txt files to 'scraped_data' folder.")
        return False
        
    print(f"   Loaded {len(documents)} documents.")

    # 2. Split Text (Optimized for better context)
    print("2. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, 
        chunk_overlap=350,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   Created {len(chunks)} chunks.")

    # 3. Create Embeddings (Using Free HuggingFace Model - No API Key needed)
    print("3. Creating Embeddings (this runs locally on CPU)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    # 4. Save to FAISS
    print("4. Saving to Vector DB...")
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(DB_PATH)
    print("--- INGESTION COMPLETE ---")
    return True

def get_groq_response(query):
    """
    Retrieves context from DB and sends it to Groq Llama 3 with optimized prompting.
    """
    # 1. Initialize Embeddings (Must be same as ingestion)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # 2. Load Vector DB
    db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 3. Initialize Groq LLM with optimized settings for accuracy
    llm = ChatGroq(
        model="qwen/qwen3-32b", 
        temperature=0.05,
        max_tokens=3000  # Increased to prevent truncation of thinking blocks
    )

    # 4. Detect university from query and create filtered retriever
    detected_university = detect_university(query)
    
    if detected_university:
        # Filter by university metadata for targeted search
        print(f"   [Filtering by university: {detected_university.upper()}]")
        retriever = db.as_retriever(
            search_kwargs={
                "k": 5,
                "filter": {"university": detected_university}
            }
        )
    else:
        # No university detected - search all documents
        retriever = db.as_retriever(search_kwargs={"k": 5})

    # 5. Enhanced Prompt Template for Students
    template = """You are a helpful university assistant specifically designed to help students with their academic queries. Your goal is to provide clear, accurate, and student-friendly responses.

Context from university documents:
{context}

Student Question: {question}

Instructions for your response:
1. Answer the question directly and accurately based on the provided context
2. If the context contains the information, provide specific details including:
   - Exact dates, deadlines, or timeframes
   - Specific requirements, procedures, or steps
   - Contact information or relevant departments if mentioned
   - Any important conditions or prerequisites
3. If the context doesn't fully answer the question, clearly state: "Based on the available information, [provide what you know], but I recommend contacting [relevant department/office] for complete details."
4. Use clear, concise, simple language that students can easily understand
5. Organize information with bullet points or numbered steps when listing multiple items only if required
6. Be encouraging and supportive in tone
7. Don't generate thinking text just provide the answer
8. you can use bullet points with line break for better readability 
9. Dont use '*' or '-' or '##' in response 
10. Dont response anything negative or offensive
11. Dont response anything that is not related to the question

Your Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 6. Run Query
    response = chain.invoke(query)
    
    # Clean thinking tags manually (handling multiple variations, case-insensitive)
    # 1. Closed tags
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Unclosed tags (start found but no end - likely truncation)
    # Regex will match from the start tag to the end of the string
    response = re.sub(r'<think>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<thought>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove requested symbols "**" and leading "-"
    response = response.replace('**', '')
    
    # Split into lines to clean line-start bullets safely
    lines = response.splitlines()
    cleaned_lines = []
    for line in lines:
        sline = line.strip()
        # Remove leading dash if present
        if sline.startswith('- '):
            sline = sline[2:]
        elif sline.startswith('-'):
            sline = sline[1:]
        cleaned_lines.append(sline)
        
    response = "\n".join(cleaned_lines).strip()
    
    return response

if __name__ == "__main__":
    # CHECK: Does the database exist? If not, create it.
    if not os.path.exists(DB_PATH):
        print("Database not found. Creating it now...")
        success = create_vector_db()
        if not success:
            sys.exit()
    
    # Chat Loop
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