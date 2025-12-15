from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
import os
import uuid
from typing import Dict

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

app = FastAPI(title="AWS MCP Chat API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store sessions
sessions: Dict[str, dict] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

def get_or_create_session(session_id: str = None):
    """Get existing session or create new one."""
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    # Create new session
    new_session_id = session_id or str(uuid.uuid4())
    
    try:
        client = MCPClient.from_config_file("aws_doc_mcp.json")
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        agent = MCPAgent(llm=llm, client=client, max_steps=15, memory_enabled=True)
        
        sessions[new_session_id] = {
            "agent": agent,
            "client": client,
            "messages": []
        }
        
        return sessions[new_session_id]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AWS MCP Chat API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    try:
        session = get_or_create_session(request.session_id)
        session_id = request.session_id or list(sessions.keys())[-1]
        
        # Get response from agent
        response = await session["agent"].run(request.message)
        
        # Store messages
        session["messages"].append({"role": "user", "content": request.message})
        session["messages"].append({"role": "assistant", "content": response})
        
        return ChatResponse(response=response, session_id=session_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/new", response_model=SessionResponse)
async def create_session():
    """Create a new session."""
    try:
        session_id = str(uuid.uuid4())
        get_or_create_session(session_id)
        return SessionResponse(session_id=session_id, message="Session created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/{session_id}/clear", response_model=SessionResponse)
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        sessions[session_id]["agent"].clear_conversation_history()
        sessions[session_id]["messages"] = []
        return SessionResponse(session_id=session_id, message="History cleared successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        client = sessions[session_id]["client"]
        if client and client.sessions:
            await client.close_all_sessions()
        
        del sessions[session_id]
        return SessionResponse(session_id=session_id, message="Session deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/messages")
async def get_messages(session_id: str):
    """Get message history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"session_id": session_id, "messages": sessions[session_id]["messages"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)