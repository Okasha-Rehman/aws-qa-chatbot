import streamlit as st
import httpx
import asyncio

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AWS MCP Chat", 
    page_icon="🤖", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.backend_ready = False

async def check_backend():
    """Check if backend is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/", timeout=2.0)
            return response.status_code == 200
    except:
        return False

async def create_session():
    """Create a new session."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_URL}/session/new", timeout=10.0)
            if response.status_code == 200:
                return response.json()["session_id"]
    except Exception as e:
        st.error(f"Failed to create session: {str(e)}")
    return None

async def send_message(message: str):
    """Send message to backend."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/chat",
                json={"message": message, "session_id": st.session_state.session_id},
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return None

async def clear_history():
    """Clear conversation history."""
    if not st.session_state.session_id:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/session/{st.session_state.session_id}/clear",
                timeout=10.0
            )
            if response.status_code == 200:
                st.session_state.messages = []
                st.success("History cleared!")
    except Exception as e:
        st.error(f"Failed to clear history: {str(e)}")

async def reset_session():
    """Reset session."""
    if st.session_state.session_id:
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{API_URL}/session/{st.session_state.session_id}",
                    timeout=10.0
                )
        except:
            pass
    
    st.session_state.session_id = None
    st.session_state.messages = []
    st.rerun()

# Check backend status
backend_status = asyncio.run(check_backend())
st.session_state.backend_ready = backend_status

# Header
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("🤖 AWS Documentation Chat")
with col2:
    if st.button("🗑️ Clear History"):
        asyncio.run(clear_history())
        st.rerun()
with col3:
    if st.button("🔄 Reset Session"):
        asyncio.run(reset_session())

# Backend status indicator
if not backend_status:
    st.error("⚠️ Backend not running! Start backend with: `uv run uvicorn backend:app --reload`")
    st.stop()
else:
    st.success("✅ Backend connected")

# Create session if needed
if not st.session_state.session_id:
    session_id = asyncio.run(create_session())
    if session_id:
        st.session_state.session_id = session_id
    else:
        st.error("Failed to create session")
        st.stop()

st.markdown("---")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about AWS..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = asyncio.run(send_message(prompt))
            if result:
                response = result["response"]
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()