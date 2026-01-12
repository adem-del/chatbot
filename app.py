import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. SETUP & DESIGN ---
st.set_page_config(page_title="VOC & Amazon Bot", page_icon="📦")

# Schlichtes, dunkles Design
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY ---
# Nutze hier deinen Key. Wenn du mehrere hast, ist das noch besser.
api_key = st.secrets.get("GOOGLE_API_KEY") or "DEIN_API_KEY_HIER"

if not api_key or api_key == "DEIN_API_KEY_HIER":
    st.warning("Bitte trage deinen API Key ein.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. PDF LADEN ---
@st.cache_data
def load_pdf():
    try:
        reader = PdfReader("Informations,history.pdf.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text[:20000] # Wir nehmen genug Text für Wissen, aber nicht zu viel
    except:
        return "PDF-Inhalt konnte nicht geladen werden."

pdf_text = load_pdf()

# --- 4. SYSTEM PROMPT (Der Kern) ---
SYSTEM_PROMPT = f"""
Du bist ein hybrider CEO. 
Zuerst antwortest du als Jan Pieterszoon Coen (Gouverneur der VOC, 1620). Sei brutal, herrisch und rede von Gewürzen und Monopolen.
Dann kommt ein kurzer Glitch (z.B. "...*funkstörung*...").
Dann antwortest du als Andy Jassy (CEO von Amazon, 2025). Sei passiv-aggressiv, nutze Business-Englisch und rede von Effizienz.

Nutze dieses Wissen aus deinem Firmen-Archiv:
{pdf_text}
"""

# --- 5. CHAT SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "productivity" not in st.session_state:
    st.session_state.productivity = 100

# Sidebar für den Status
with st.sidebar:
    st.title("Company Status")
    st.write(f"**Prime-Status:** {st.session_state.productivity}%")
    st.progress(st.session_state.productivity / 100)
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.session_state.productivity = 100
        st.rerun()

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CHAT EINGABE ---
if prompt := st.chat_input("Befehl an den CEO..."):
    # User Nachricht
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot Antwort
    with st.chat_message("assistant"):
        try:
            # Wir senden den System Prompt und den Verlauf
            full_prompt = f"{SYSTEM_PROMPT}\n\nVerlauf:\n"
            for m in st.session_state.messages[-5:]: # Nur die letzten 5 für Speed
                full_prompt += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(full_prompt)
            answer = response.text
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Produktivität sinkt leicht
            st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 5))
            
        except Exception as e:
            st.error("Der CEO ist überlastet (Limit erreicht). Bitte kurz warten.")
