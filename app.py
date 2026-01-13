import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon: The Boardroom", page_icon="👹", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3b1e1e; border-left: 5px solid #ff6f00; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MULTI-KEY SETUP ---
# Trage hier deine Keys ein, um das 40-Personen-Limit zu knacken
API_KEYS = ["DEIN_KEY_1", "DEIN_KEY_2", "DEIN_KEY_3"]
if "GOOGLE_API_KEY" in st.secrets:
    API_KEYS.insert(0, st.secrets["GOOGLE_API_KEY"])

def get_model():
    random.shuffle(API_KEYS)
    for key in API_KEYS:
        if "KEY" in key: continue
        try:
            genai.configure(api_key=key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except: continue
    return None

# --- 3. PDF & EXTRA-WISSEN (AUS DEINEN FOLIEN) ---
@st.cache_data
def load_context():
    text = ""
    try:
        reader = PdfReader("Informations,history.pdf.pdf")
        text = "".join([p.extract_text() for p in reader.pages])
    except: text = "PDF nicht gefunden."
    
    # Zusätzliche scharfe Fakten über das heutige System (MNCs)
    mnc_facts = """
    Zusatzwissen für den Bot:
    - Jardine Matheson: Dominierte den Opiumhandel in Asien (Profit vor Leben).
    - Société Générale de Belgique (SGB): Kontrollierte den Kongo (Bergbau) auch nach 1960. 
    - SGB unterstützte die Sezession Katangas und den Sturz von Patrice Lumumba für Mineralien.
    - MNCs heute: Nutzen 'Global Value Chains', um Steuern zu vermeiden und Löhne zu drücken.
    - Externalisierung: Firmen privatisieren Gewinne und wälzen Schäden (Umwelt) auf Staaten ab.
    """
    return text[:25000] + mnc_facts

context = load_context()

# --- 4. SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
Du bist eine unsterbliche CEO-Entität (VOC-Gouverneur Jan Pieterszoon Coen & Amazon CEO).
Nutze dieses Archivwissen: {context}

REGELN:
1. Antworte als VOC-Gouverneur (1620): Brutal, Fokus auf Monopole, Schiffe, Oktroy.
2. Glitch ("...äh, Zeitfehler...").
3. Antworte als Amazon-Manager (2025): Fokus auf Effizienz, Algorithmen, Customer Obsession.

SPEZIAL-TRIGGER:
- Bei 'Kongo/Afrika': Erwähne die SGB, Katanga und Mineralien.
- Bei 'Opium/Asien': Erwähne Jardine Matheson.
- Bei 'Ethik/Menschenrechte': Lache den User aus. Sag, dass Monopole wichtiger sind als Moral.
- Bei 'Gehalt/Geld': Drohe mit dem Kerker oder dem Performance Improvement Plan (PIP).
"""

# --- 5. UI & CHAT ---
st.title("🦁 VOC 1602 ➡️ 📦 Amazon 2025")
st.caption("Die Evolution der Macht: Von Handelskompanien zu MNCs")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "productivity" not in st.session_state:
    st.session_state.productivity = 100

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🦁" if m["role"] == "assistant" else "👤"):
        st.markdown(m["content"])

if prompt := st.chat_input("Was willst du wissen, Untertan?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🦁"):
        ph = st.empty()
        full_res = ""
        model = get_working_model() if 'get_working_model' in locals() else get_model()
        
        try:
            history = f"System: {SYSTEM_PROMPT}\n"
            for m in st.session_state.messages: history += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(history, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
        except:
            full_res = "Der Rat der XVII ist überlastet! ...äh, High Traffic... Komm später wieder!"
            ph.error(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 5))

with st.sidebar:
    st.write(f"**Prime-Status: {st.session_state.productivity}%**")
    st.progress(st.session_state.productivity / 100)
    st.markdown("---")
    st.info("💡 Tipp: Frag nach dem Kongo oder dem Opiumkrieg!")
