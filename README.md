# AWS MCP FastAPI Chatbot

AI-powered chatbot for AWS documentation using FastAPI backend and Streamlit frontend.

## Features
- FastAPI REST API backend
- Streamlit web interface
- AWS documentation search via MCP
- Session management
- Conversation memory

## Setup

1. Clone repository:
```bash
git clone (https://github.com/Okasha-Rehman/aws-qa-chatbot)
cd aws-mcp-fastapi
```

2. Install dependencies:
```bash
uv sync
```

3. Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

4. Run backend:
```bash
uv run uvicorn backend:app --reload
```

5. Run frontend (new terminal):
```bash
uv run streamlit run frontend.py
```

## Access
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Tech Stack
- FastAPI
- Streamlit
- LangChain
- Groq LLM
- MCP (Model Context Protocol)
