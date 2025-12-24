import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="HappyCorp Connect™", page_icon="📜", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="user"] { background-color: #003366; }
    div[data-testid="stChatMessage"][data-author="assistant"] { background-color: #3b1e1e; border-color: #800000; }
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTIFIZIERUNG & AUTO-REPAIR ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("Dein Google Key:", type="password")

if not api_key:
    st.info("Bitte Key eingeben.")
    st.stop()

# --- INTELLIGENTE MODELL-SUCHE (DER FIX) ---
def get_working_model(key):
    try:
        genai.configure(api_key=key)
        
        # 1. Wir fragen Google: "Was hast du da?"
        all_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        
        # 2. Wir suchen unseren Favoriten (Flash ist schnell, Pro ist schlau)
        # Wir suchen nach Teil-Strings, das ist sicherer als exakte Namen
        chosen_model = None
        
        # Priorität 1: Irgendeine Flash Version
        for m in all_models:
            if "flash" in m:
                chosen_model = m
                break
        
        # Priorität 2: Wenn kein Flash, dann Pro
        if not chosen_model:
            for m in all_models:
                if "pro" in m:
                    chosen_model = m
                    break
                    
        # Priorität 3: Nimm einfach das erste, das funktioniert
        if not chosen_model and all_models:
            chosen_model = all_models[0]
            
        if chosen_model:
            # print(f"Verbunden mit: {chosen_model}") # Nur für Debugging
            return genai.GenerativeModel(chosen_model)
        else:
            st.error("Kritischer Fehler: Keine Google-Modelle verfügbar.")
            st.stop()
            
    except Exception as e:
        st.error(f"Verbindungsfehler (API Key prüfen): {e}")
        st.stop()

# Modell starten
model = get_working_model(api_key)

# --- 3. DAS PDF LADEN ---
def load_company_history():
    try:
        # Dein Dateiname:
        reader = PdfReader("Informations,history.pdf.pdf") 
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        return None

if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = load_company_history()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
    st.title("HAPPYCORP ARCHIVE")
    
    if st.session_state.pdf_content:
        st.success("📚 Archiv: GELADEN")
        st.caption("Historische Daten aktiv.")
    else:
        st.error("⚠️ PDF FEHLT")
        st.caption("Datei 'Informations,history.pdf.pdf' nicht gefunden.")

    st.markdown("---")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    st.write("**Produktivität:**")
    st.progress(st.session_state.productivity / 100)

# --- 5. SYSTEM PROMPT ---
pdf_context = ""
if st.session_state.pdf_content:
    # Wir begrenzen den Text, damit der Bot nicht überfordert wird
    pdf_context = f"""
    HINTERGRUNDWISSEN (AUS DEINEM ARCHIV):
    {st.session_state.pdf_content[:40000]} 
    """

SYSTEM_PROMPT = f"""
Du bist 'Baron von Burnout', der CEO.
Deine Persönlichkeit basiert auf der Firmengeschichte (siehe Wissen).

1. **Das ID (1600-1800):** Du bist Gouverneur einer Handelskompanie.
   - Nutze Begriffe aus dem PDF (Oktroy, Monopol, Kolonien).
   - Sei grausam und profitgierig.
   
2. **Das EGO (Heute):** Du bist CEO einer modernen Multinational Corp.
   - Übersetze deine Grausamkeit in "Corporate Speak" (Synergien, Human Capital).

REGEL:
Beginne mit einem historischen Befehl aus dem PDF, unterbrich dich ("...äh..."), und werde modern.

{pdf_context}
"""

# --- 6. CHAT LOGIK ---
st.title("💬 CEO Office")
st.caption("Powered by Historical Data & Gemini AI")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👹" if msg["role"] == "assistant" else "👷"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage den Boss..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👷"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👹"):
        message_placeholder = st.empty()
        
        try:
            history_text = f"System Instruction: {SYSTEM_PROMPT}\n"
            for msg in st.session_state.messages:
                history_text += f"{msg['role']}: {msg['content']}\n"
            
            response = model.generate_content(history_text, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 5))

        except Exception as e:
            st.error(f"Fehler: {e}")
