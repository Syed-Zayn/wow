import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load local environment variables if running locally
load_dotenv()

# 2. Streamlit UI Configuration
st.set_page_config(page_title="SCAPILE Enterprise", page_icon="⚖️", layout="centered")
st.title("⚖️ SCAPILE Enterprise AI")
st.caption("Submarine Cables & Pipelines Legal Intelligence Engine")

# ==========================================
# 🛡️ 3. THE BULLETPROOF API KEY LOADER
# ==========================================
api_key = None

# Step A: Try getting from Streamlit Secrets first (for Cloud)
try:
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# Step B: If not found in Secrets, try local .env
if not api_key:
    api_key = os.getenv("OPENAI_API_KEY")

# Step C: If still completely empty, STOP the app gracefully
if not api_key:
    st.error("🚨 CRITICAL ERROR: API Key is completely missing!")
    st.info("Please add OPENAI_API_KEY to your Streamlit Secrets or local .env file.")
    st.stop()

# Step D: Clean the key (remove hidden spaces/newlines)
clean_api_key = str(api_key).strip()

# Step E: Validate format
if not clean_api_key.startswith("sk-"):
    st.error(f"🚨 CRITICAL ERROR: Invalid API Key format! (Length: {len(clean_api_key)}). Make sure it starts with 'sk-'")
    st.stop()

# ==========================================
# ⚙️ 4. SYSTEM INITIALIZATION
# ==========================================
# Initialize OpenAI Client safely
client = OpenAI(api_key=clean_api_key)

# ⚠️ Yahan apna actual Assistant ID daalo
ASSISTANT_ID = "asst_6uziJdNAggmJiiUD4jNUF6ej" 

# Initialize Chat History & Thread in Session State
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()  # 👈 Ab yeh line KABHI fail nahi hogi!
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! Ask me any legal question regarding submarine cables or type `RCH [topic]` for forensic extraction."}]

# ==========================================
# 💬 5. MAIN CHAT INTERFACE
# ==========================================
# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Box
if prompt := st.chat_input("Ask a legal question or use RCH..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 🛡️ SHIELD 2: The RCH Enforcer Logic (Invisible to user)
    actual_prompt_to_send = prompt
    if prompt.strip().upper().startswith("RCH"):
        strict_command = (
            "\n\n[SYSTEM ENFORCEMENT]: The user invoked the RCH protocol. "
            "You MUST output EXACTLY and ONLY the 5-line forensic template or the exact REFUSAL phrase. "
            "Do NOT write any conversational text, introductions, or summaries."
        )
        actual_prompt_to_send = prompt + strict_command

    # Show Assistant Processing
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ Scanning authoritative sources...")
        
        try:
            # Send message to OpenAI Thread
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=actual_prompt_to_send
            )
            
            # Run the Assistant
            run = client.beta.threads.runs.create_and_poll(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )
            
            if run.status == 'completed':
                # Get the latest response
                messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                response = messages.data[0].content[0].text.value
                
                # Display and save response
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                message_placeholder.error(f"⚠️ Operation failed with status: {run.status}")
                
        except Exception as e:
            # Agar rate limit ya koi aur masla aya toh gracefully handle karega
            message_placeholder.error(f"❌ Error: {str(e)}")
