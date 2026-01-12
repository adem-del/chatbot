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

# --- 2. AUTHENTIFIZIERUNG ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("Dein Google Key:", type="password")

# --- 3. NOTFALL-SPRÜCHE (FALLBACK) ---
# Falls Google abstürzt oder das Limit erreicht ist, nimmt er einen von diesen:
FALLBACK_RESPONSES = [
    "Das Gewürz-Lager ist leer! ...äh, buffering... Server-Überlastung. Geh zurück an die Arbeit!",
    "Ich lasse dich auspeitschen! ...ping timeout... Dein Performance-Review wird verschoben.",
    "Schweig, du unwürdiger Matrose! ...404 Error... Bitte wende dich an den HR-Chatbot.",
    "Mehr Nelken für Amsterdam! ...sync error... Wir skalieren gerade unsere Cloud-Infrastruktur.",
    "Du wagst es, den Gouverneur zu stören? ...low bandwidth... Deine Anfrage ist in der Warteschlange (Position 9999).",
    "Ab in den Kerker mit dir! ...system update... Bitte installiere die neueste Version der App.",
    "Wir brauchen mehr Sklaven für die Plantagen! ...glitch... Ich meine: Wir stellen neue Fulfillment Associates ein."
]

# --- 4. MODELL & PDF ---
def get_model(key):
    if not key: return None
    try:
        genai.configure(api_key=key)
        # Wir erzwingen FLASH, das hat höhere Limits als Pro
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_model(api_key)

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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("HANDELS-IMPERIEN")
    st.caption("1602 (VOC) ➡️ 2025 (Amazon)")
    
    if st.session_state.pdf_content:
        st.success("Datenbank: ONLINE")
    else:
        st.warning("⚠️ PDF fehlt (Backup Modus)")

    st.markdown("---")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    
    st.write("**Prime-Status:**")
    st.progress(st.session_state.productivity / 100)
    
    if st.session_state.productivity < 30:
        st.error("⚠️ KÜNDIGUNG EINGELEITET")

# --- 6. PROMPT ---
pdf_context = ""
if st.session_state.pdf_content:
    pdf_context = f"FAKTEN AUS PDF: {st.session_state.pdf_content[:20000]}"

SYSTEM_PROMPT = f"""
Du bist CEO (1620 VOC & 2025 Amazon).
REGEL:
1. Beginne als VOC-Gouverneur (brutal, Gewürze, Schiffe). Drohe dem User.
2. Unterbrich dich ("...äh, Zeitfehler...").
3. Wiederhole es als Amazon-Manager (Corporate Speak, Fulfillment, Effizienz).

{pdf_context}
"""

# --- 7. CHAT LOGIK (MIT NOTFALL-NETZ) ---
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

        # HIER IST DER RETTUNGSANKER
        try:
            if not model: raise Exception("Kein Model")
            
            history_text = f"System: {SYSTEM_PROMPT}\n"
            for msg in st.session_state.messages:
                history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Wir versuchen die echte KI
            response = model.generate_content(history_text, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
        except Exception as e:
            # WENN GOOGLE FEHLER MELDET (429 QUOTA), GEHEN WIR HIER REIN
            # Wir tun so, als würde er "denken"
            time.sleep(1) 
            # Wir nehmen einen zufälligen Spruch aus der Liste oben
            full_response = random.choice(FALLBACK_RESPONSES)
            # Wir fügen noch einen Hinweis für dich hinzu (nur du siehst das quasi am Text)
            full_response += " *(System: Offline-Modus aktiv)*"
        
        # Antwort anzeigen und speichern
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 6))
