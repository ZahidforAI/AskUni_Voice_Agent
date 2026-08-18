# AskUni AI Voice Agent 🤖🎓

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/zahidforai/askuni-voice-agent)
**[Try the Live Demo Here!](https://huggingface.co/spaces/zahidforai/askuni-voice-agent)**

**AskUni** is an intelligent, voice-powered university assistant designed to help students navigate the complex world of higher education. Powered by **Groq (Llama 3)** and **RAG (Retrieval-Augmented Generation)** technology, it provides accurate, context-aware answers about various universities, compares programs, and even navigates to specific official university pages for you.

![Project Screenshot](placeholder-image.png)
*(Add your project screenshot here)*

## 🚀 Features

- **🗣️ Voice & Text Interaction:**  
  Ask questions naturally using voice or text. The agent understands context and intent.

- **📚 Multi-University Support:**  
  Comprehensive knowledge base for major universities including:
  - SMIU (Sindh Madressatul Islam University)
  - NED University of Engineering & Technology
  - IBA (Institute of Business Administration)
  - UOK (University of Karachi)
  - FAST NUCES
  - SZABIST
  - DHA Suffa University
  - DUET (Dawood University)

- **🧠 Advanced RAG Architecture:**  
  Uses **LangChain**, **FAISS Vector Database**, and **HuggingFace Embeddings** to retrieve accurate information from your local data files (`.txt`), minimizing hallucinations.

- **⚡ Blazing Fast Responses:**  
  Powered by the **Groq API** (Llama 3 models) for near-instant inference speeds.

- **🔗 Smart Navigation:**  
  Automatically detects user intent and opens relevant official pages (e.g., "Open admission page for NED", "Show me the fee structure of FAST").

- **🌐 WebSocket Integration:**  
  Real-time, bidirectional communication for a seamless conversational experience.

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, WebSockets
- **AI/LLM:** Groq API (Llama 3 70B/8B), LangChain
- **Vector DB:** FAISS (Facebook AI Similarity Search)
- **Embeddings:** HuggingFace (`sentence-transformers/all-mpnet-base-v2`)
- **Frontend:** HTML5, JavaScript (WebSocket client)
- **Deployment:** Docker, Render

## 📋 Prerequisites

- Python 3.9+
- [Groq API Key](https://console.groq.com/) (Free beta access available)

## 📦 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/AskUni-Voice-Agent.git
   cd AskUni-Voice-Agent
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Prepare Your Data**
   - Place your university data files (`.txt` format) inside the `UNIVERSITY/` folder.
   - Example structure:
     ```
     UNIVERSITY/
     ├── SMIU/
     │   ├── admission.txt
     │   └── history.txt
     ├── NED/
     │   └── programs.txt
     └── ...
     ```

## 🚀 Usage

1. **Start the Server**
   ```bash
   python main.py
   ```
   *The server will automatically generate the vector database (`faiss_index`) on the first run if it doesn't exist.*

2. **Access the Application**
   Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

3. **Interact**
   - Click the microphone button to speak or type your query.
   - Example queries:
     - *"What are the admission requirements for CS and SE at FAST?"*
     - *"Compare the fee structure of IBA and SZABIST."*
     - *"Open the student portal for SMIU."*

## 🐳 Docker Deployment

You can also run AskUni using Docker:

1. **Build the Image**
   ```bash
   docker build -t askuni .
   ```

2. **Run the Container**
   ```bash
   docker run -p 8080:8080 --env-file .env askuni
   ```

## 📂 Project Structure

```
AskUni-Voice-Agent/
├── UNIVERSITY/          # Folder containing knowledge base .txt files
├── faiss_index/         # Generated Vector Database (created automatically)
├── main.py              # FastAPI server & WebSocket handling
├── groq_rag.py          # RAG implementation (LangChain + Groq)
├── index.html           # Frontend UI
├── Dockerfile           # Docker configuration
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (API Keys)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Created by [Your Name]**  
*FYP Project 2024*
