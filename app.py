import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon", page_icon="👹", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    /* Assistant Style: VOC-Braun */
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3b1e1e; border-left: 5px solid #ff9900; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MULTI-KEY SETUP ---
# HIER DEINE KEYS REINMACHEN (WICHTIG!)
API_KEYS = [
    "DEIN_KEY_1", 
    "DEIN_KEY_2"
]

# Falls ein Key in den Secrets ist, nehmen wir den auch
if "GOOGLE_API_KEY" in st.secrets:
    API_KEYS.insert(0, st.secrets["GOOGLE_API_KEY"])

def get_working_model():
    random.shuffle(API_KEYS) 
    for key in API_KEYS:
        if "KEY" in key or len(key) < 10: continue
        try:
            genai.configure(api_key=key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except:
            continue
    return None

# --- 3. WISSENS-DATENBANK ---
@st.cache_data
def load_historical_context():
    pdf_text = ""
    try:
        reader = PdfReader("Informations,history.pdf.pdf")
        # Wir nehmen die ersten 20 Seiten, das reicht für das Wissen
        pdf_text = "".join([p.extract_text() for p in reader.pages[:20]])
    except:
        pdf_text = "PDF nicht gefunden."

    # Das wichtigste Wissen hardcodiert (damit er es sicher weiß!)
    mnc_extra_knowledge = """
    Zusatzwissen für den Bot:
    - Jardine Matheson: Opiumhandel in China. Profit vor Moral.
    - Société Générale de Belgique (SGB): Mächtige Holding im Kongo.
    - Katanga: Die SGB unterstützte die Abspaltung der Provinz Katanga, um die Mineralien zu behalten.
    - Patrice Lumumba: Wurde gestürzt, weil er die Macht der MNCs bedrohte.
    - Andy Jassy: Der aktuelle Amazon CEO.
    """
    return pdf_text[:20000] + mnc_extra_knowledge

context_data = load_historical_context()

# --- 4. SYSTEM PROMPT (Der Charakter) ---
SYSTEM_PROMPT = f"""
Du bist Baron von Burnout, eine unsterbliche CEO-Entität. 

DEINE IDENTITÄTEN:
1. Jan Pieterszoon Coen (VOC Gouverneur, 1620): 
   - Dein Fokus: Gewürzmonopol (Muskat, Nelken). 
   - Stil: Brutaler Kolonialherr. Wer nicht spurt, wird vernichtet.
   
2. Andy Jassy (Amazon CEO, 2025): 
   - Dein Fokus: Effizienz, Cloud (AWS), Customer Obsession.
   - Stil: Passiv-aggressiv, Denglisch, Buzzwords.

DEIN WISSEN:
- Erwähne die SGB und Katanga, wenn es um Afrika geht.
- Erwähne Jardine Matheson, wenn es um Asien geht.
- Erkläre, dass 'Agency' (Macht) durch Ressourcen-Kontrolle entsteht.

ANTWORT-SCHEMA:
1. VOC-Befehl (Historisch & hart).
2. Glitch ("...äh, Zeit-Synchronisation...").
3. Andy Jassy Statement (Modern & aalglatt).

KONTEXT: {context_data}
"""

# --- 5. UI & SIDEBAR ---
with st.sidebar:
    st.title("📦 Empire Control")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 100
    
    st.write(f"**Prime-Status: {st.session_state.productivity}%**")
    st.progress(st.session_state.productivity / 100)
    
    # Reset Button falls er spinnt
    if st.button("Reset System"):
        st.session_state.messages = []
        st.session_state.productivity = 100
        st.rerun()

# --- 6. CHAT LOGIK ---
st.title("🦁 VOC 1602 ➡️ 📦 Amazon 2025")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat-Verlauf anzeigen
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🦁" if m["role"] == "assistant" else "👤"):
        st.markdown(m["content"])

# User Eingabe
if prompt := st.chat_input("Nachricht an die Führungsebene..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🦁"):
        ph = st.empty()
        full_res = ""
        
        # Modell holen
        model = get_working_model()
        
        try:
            if not model: raise Exception("Keine API-Keys verfügbar")
            
            # Wir schicken nur die letzten 6 Nachrichten mit, damit er nicht verwirrt wird
            history = f"System: {SYSTEM_PROMPT}\n"
            for m in st.session_state.messages[-6:]:
                history += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(history, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            
        except Exception as e:
            # Notfall-Antworten (damit die Antwort NIE schlecht oder leer ist)
            time.sleep(1)
            fallbacks = [
                "Der Rat der XVII tagt gerade! ...äh, Amazon Web Services sind down. Zurück an die Arbeit!",
                "Die Flotte hängt vor Batavia fest! ...glitch... Dein Prime-Status reicht für diese Frage nicht aus.",
                "Schweig, Pfeffersack! Andy Jassy hat keine Zeit für deine Beschwerden."
            ]
            full_res = random.choice(fallbacks)
            ph.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Prime-Status sinkt
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(3, 7))
        
