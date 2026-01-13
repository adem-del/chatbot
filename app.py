import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    
    /* Historisch (VOC) */
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3e2723; 
        border-color: #ff6f00; 
        border-left: 5px solid #ff6f00;
    }
    
    /* User */
    div[data-testid="stChatMessage"][data-author="user"] { background-color: #0d47a1; }
</style>
""", unsafe_allow_html=True)

# --- 2. MULTI-KEY SETUP (DEINE VERSICHERUNG) ---

# Hier trägst du alle deine Keys ein. Er nimmt den ersten, der funktioniert.
API_KEYS = [
    # Key 1 (Dein Haupt-Key)
    "AIzaSyD8Dq-QVgj1jPrFeGZSV45zcyF-Ld7lvkY", 
    
    # Key 2 (Reserve, falls Key 1 leer ist)
    "AIzaSyAR4eXx5jiWME-mxDaODKC6pIMQnb4cAsM",
    
    # Key 3 (Notfall)
    "AIzaSyCnLWRYx-ZZ6Aomfr3ykQyehw0GDTvzXQ8"
]

# Wir schauen auch, ob in den Streamlit Secrets einer liegt und packen ihn dazu
if "GOOGLE_API_KEY" in st.secrets:
    API_KEYS.insert(0, st.secrets["GOOGLE_API_KEY"])

# --- 3. NOTFALL-SPRÜCHE (OFFLINE MODUS) ---
FALLBACK_RESPONSES = [
    "Das Gewürz-Lager ist leer! ...äh, buffering... Server-Überlastung.",
    "Ich lasse dich auspeitschen! ...ping timeout... Dein Performance-Review wird verschoben.",
    "Schweig, du unwürdiger Matrose! ...404 Error... Bitte wende dich an den HR-Chatbot.",
    "Mehr Nelken für Amsterdam! ...sync error... Wir skalieren gerade unsere Cloud-Infrastruktur.",
    "Du wagst es, den Gouverneur zu stören? ...low bandwidth... Deine Anfrage ist in der Warteschlange.",
    "Ab in den Kerker mit dir! ...system update... Bitte installiere die neueste Version der App.",
    "Wir brauchen mehr Sklaven! ...glitch... Ich meine: Wir stellen neue Fulfillment Associates ein."
]

# --- 4. INTELLIGENTE VERBINDUNG ---
def get_working_model():
    # Wir testen jeden Key in der Liste
    for key in API_KEYS:
        if "HIER_KEY" in key: continue # Überspringt die Platzhalter
        
        try:
            genai.configure(api_key=key)
            # Wir nehmen Flash, weil es schneller ist und höhere Limits hat
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model
        except Exception:
            continue # Wenn Key kaputt, nimm den nächsten
            
    return None # Wenn KEIN Key geht

model = get_working_model()

# --- 5. PDF LADEN ---
def load_history():
    try:
        reader = PdfReader("Informations,history.pdf.pdf") 
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        return None

if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = load_history()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("HANDELS-IMPERIEN")
    st.caption("1602 (VOC) ➡️ 2025 (Amazon)")
    
    if st.session_state.pdf_content:
        st.success("Datenbank: ONLINE")
    else:
        st.warning("⚠️ PDF fehlt (Backup Modus)")

    st.markdown("---")
    
    # Status Anzeige
    if model:
        st.success("🟢 KI-Verbindung: Stabil")
    else:
        st.error("🔴 KI-Verbindung: Offline (Notfall-Modus)")

    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    
    st.write("**Prime-Status:**")
    st.progress(st.session_state.productivity / 100)
    
    if st.session_state.productivity < 30:
        st.error("⚠️ KÜNDIGUNG EINGELEITET")

# --- 7. PROMPT ---
pdf_context = ""
if st.session_state.pdf_content:
    pdf_context = f"FAKTEN AUS PDF: {st.session_state.pdf_content[:25000]}"

SYSTEM_PROMPT = f"""
Du bist CEO (1620 VOC & 2025 Amazon).
REGEL:
1. Beginne als VOC-Gouverneur (brutal, Gewürze, Schiffe). Drohe dem User.
2. Unterbrich dich ("...äh, Zeitfehler...").
3. Wiederhole es als Amazon-Manager (Corporate Speak, Fulfillment, Effizienz).

{pdf_context}
"""

# --- 8. CHAT LOGIK ---
st.title("📦 Von Gewürzen zu Paketen")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👑" if msg["role"] == "assistant" else "📦"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nachricht an den Boss..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="📦"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👑"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            if not model: raise Exception("Kein Model")
            
            history_text = f"System: {SYSTEM_PROMPT}\n"
            for msg in st.session_state.messages:
                history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Streaming Versuch
            response = model.generate_content(history_text, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
        except Exception as e:
            # FALLBACK WENN ALLE KEYS VERSAGEN ODER LIMIT ERREICHT
            time.sleep(0.8) 
            full_response = random.choice(FALLBACK_RESPONSES)
            full_response += " *(System: Offline-Modus)*"
        
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 6))
