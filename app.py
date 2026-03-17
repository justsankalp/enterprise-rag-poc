import streamlit as st
import asyncio
from google.genai import types

# Import the existing pipeline from your agent.py file
# Ensure agent.py has runner and session_service defined globally
from agent import runner, session_service 

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Save Soil Copilot", page_icon="🌱", layout="centered")
st.title("🌱 Save Soil Policy Copilot")
st.markdown("**Citation-Grade RAG System (PoC)** | Built with Google ADK & ChromaDB")
st.divider()

# --- CHAT HISTORY STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT INTERFACE ---
if prompt := st.chat_input("Ask a question about the soil policy... (e.g., 'What are the targets for Africa?')"):
    
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # We wrap the ADK async streaming logic inside a synchronous Streamlit app
        async def fetch_and_stream_response():
            global full_response  # <--- CHANGED THIS TO GLOBAL
            
            # Ensure the ADK session is active
            await session_service.create_session(
                app_name="soil_copilot",
                user_id="streamlit_user",
                session_id="session_1"
            )
            
            # Package the user prompt for the ADK
            user_message = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
            
            # Stream the response chunks from the ADK Agent
            async for event in runner.run_async(
                user_id="streamlit_user", 
                session_id="session_1", 
                new_message=user_message
            ):
                # Extract text chunks and update the UI
                if hasattr(event, 'content') and event.content.parts and event.content.parts[0].text:
                    chunk = event.content.parts[0].text
                    full_response += chunk
                    # Add a blinking cursor effect while typing
                    message_placeholder.markdown(full_response + "▌")
            
            # Final output without the cursor
            message_placeholder.markdown(full_response)

        # Execute the async function
        asyncio.run(fetch_and_stream_response())
        
        # Save to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})