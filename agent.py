import asyncio
import chromadb
from chromadb.utils import embedding_functions
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 1. Connect to the local database
chroma_client = chromadb.PersistentClient(path="./soil_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_collection(name="save_soil_policies", embedding_function=sentence_transformer_ef)

# 2. Define the retrieval function
def search_soil_policy(query: str) -> str:
    """Searches the Save Soil Policy vector database for factual policy information."""
    print(f"\n[System: Searching Vector DB for -> '{query}']")
    
    results = collection.query(query_texts=[query], n_results=2)
    
    if not results['documents'][0]:
        return "No relevant documents found in the policy book. You must state explicit uncertainty."
        
    compiled_context = ""
    for idx, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][idx]
        compiled_context += f"Fact: {doc}\nCitation: {meta['source']}, Page {meta['page']}\n\n"
        
    return compiled_context

# 3. Initialize the ADK Agent (Modern ADK allows passing functions directly to tools)
policy_agent = Agent(
    model='gemini-3-flash-preview', 
    name="SoilPolicyCopilot",
    instruction="""You are an expert environmental policy assistant. 
    1. ALWAYS use the `search_soil_policy` tool to answer user questions.
    2. NEVER invent or hallucinate information. If the tool yields no relevant data, state you do not know.
    3. You MUST append the exact source and page number to the end of every answer you provide.""",
    tools=[search_soil_policy] 
)

# 4. Set up the modern Session and Runner
session_service = InMemorySessionService()

runner = Runner(
    agent=policy_agent,
    app_name="soil_copilot",
    session_service=session_service
)

# 5. Execute using the async ADK Runner
async def run_test():
    print("Agent Initialized. Let's test the pipeline.\n")
    test_question = "What is the current scenario of soil health in the United Kingdom?"
    print(f"User Query: {test_question}\n")
    
    # Create a session explicitly
    await session_service.create_session(
        app_name="soil_copilot",
        user_id="user_123",
        session_id="session_1"
    )

    print("\n--- Final Agent Response ---")
    
    # Package the message into ADK's Content type
    user_message = types.Content(role="user", parts=[types.Part.from_text(text=test_question)])
    
    # Run the agent asynchronously and stream events
    async for event in runner.run_async(
        user_id="user_123", 
        session_id="session_1", 
        new_message=user_message
    ):
        if hasattr(event, 'content') and event.content.parts and event.content.parts[0].text:
             print(event.content.parts[0].text, end="", flush=True)
             
    print("\n")

if __name__ == "__main__":
    asyncio.run(run_test())