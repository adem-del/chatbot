import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG ---
st.set_page_config(page_title="VOC vs. Amazon", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3e2723; border-left: 5px solid #ff6f00; 
    }
    div[data-testid="stChatMessage"][data-author="user"] { background-color: #0d47a1; }
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTIFIZIERUNG (Nur 1 Key nötig) ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback für lokal
    api_key = "DEIN_KEY_HIER" # Wenn du lokal testest

# --- 3. HARDCODED ANTWORTEN (Der Trick zum Sparen) ---
# Diese Antworten kosten DICH NICHTS (kein API Limit)
STATIC_ANSWERS = {
    "hallo": "Seid gegrüßt, Pfeffersack! ...äh, Welcome Stakeholder... Was wollt Ihr?",
    "hi": "Keine Zeit für Nettigkeiten! Die Schiffe warten! ...äh, Time is money...",
    "wer bist du": "Ich bin Jan Pieterszoon Coen, Generalgouverneur der VOC! ...glitch... Ich bin der CEO von Amazon.",
    "wie geht es dir": "Schlecht! Die Muskatnuss-Preise fallen! ...äh, stock market crash... Arbeite weiter!",
    "was machst du": "Ich plane die nächste Strafexpedition nach Banda. ...äh, Markt-Expansion...",
    "test": "System läuft. Faulheit wird bestraft. ...System operational...",
}

# --- 4. FUNKTIONEN ---
def get_model(key):
    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_model(api_key)

# Caching für das PDF, damit es nicht jedes Mal neu lädt
@st.cache_data
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
    st.caption("Smart-Mode aktiv 🟢")
    
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    st.progress(st.session_state.productivity / 100)

# --- 6. PROMPT ---
pdf_text = st.session_state.pdf_content[:20000] if st.session_state.pdf_content else ""
SYSTEM_PROMPT = f"""
Du bist CEO (1620 VOC & 2025 Amazon).
1. Beginne als VOC-Gouverneur (brutal, Gewürze).
2. Unterbrich dich ("...äh, Glitch...").
3. Wiederhole als Amazon-Manager (Corporate Speak).
Fakten: {pdf_text}
"""

# --- 7. CHAT LOGIK ---
st.title("📦 VOC 1602 ➡️ Amazon 2025")
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
        ph = st.empty()
        full_res = ""
        
        # --- DER SPARTIPP ---
        # Wir machen alles klein und entfernen Leerzeichen am Rand
        clean_prompt = prompt.lower().strip().replace("?", "")
        
        # Check: Haben wir eine kostenlose Antwort parat?
        if clean_prompt in STATIC_ANSWERS:
            # JA! Wir nutzen die lokale Antwort (0 API Kosten)
            time.sleep(0.5) # Fake-Denkzeit
            full_res = STATIC_ANSWERS[clean_prompt]
            ph.markdown(full_res)
        
        else:
            # NEIN, echte Frage -> Wir müssen Google fragen
            try:
                history = f"System: {SYSTEM_PROMPT}\n"
                for m in st.session_state.messages: history += f"{m['role']}: {m['content']}\n"
                
                response = model.generate_content(history, stream=True)
                for chunk in response:
                    if chunk.text:
                        full_res += chunk.text
                        ph.markdown(full_res + "▌")
                ph.markdown(full_res)
                
            except Exception as e:
                # Notfall, falls API Limit erreicht ist
                full_res = "Der Server ist überlastet. Geh zurück an die Arbeit! (API Quota Error)"
                ph.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 6))
