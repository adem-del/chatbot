import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon: Corporate Empire", page_icon="📦", layout="wide")

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
# Füge hier so viele Keys wie möglich ein, um das 40-Personen-Limit zu bewältigen
API_KEYS = [
    "DEIN_KEY_1", 
    "DEIN_KEY_2", 
    "DEIN_KEY_3"
]

# Falls ein Key in den Streamlit-Secrets hinterlegt ist
if "GOOGLE_API_KEY" in st.secrets:
    API_KEYS.insert(0, st.secrets["GOOGLE_API_KEY"])

def get_working_model():
    random.shuffle(API_KEYS) # Lastverteilung
    for key in API_KEYS:
        if "KEY" in key or len(key) < 10: continue
        try:
            genai.configure(api_key=key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except:
            continue
    return None

# --- 3. WISSENS-DATENBANK (PDF + MNC FAKTEN) ---
@st.cache_data
def load_historical_context():
    pdf_text = ""
    try:
        reader = PdfReader("Informations,history.pdf.pdf")
        pdf_text = "".join([p.extract_text() for p in reader.pages])
    except:
        pdf_text = "PDF-Archiv nicht gefunden."

    mnc_extra_knowledge = """
    Zusatzwissen für den Bot (MNCs & Geschichte):
    - Jardine Matheson: Führte den Opiumhandel in Asien an. Profit war wichtiger als die Gesetze Chinas.
    - Société Générale de Belgique (SGB): Die mächtige Holding, die den Kongo-Bergbau kontrollierte.
    - SGB & Katanga: Sie unterstützten die Abspaltung der mineralienreichen Provinz Katanga 1960.
    - Patrice Lumumba: Wurde durch den Einfluss westlicher MNCs und Geheimdienste isoliert und gestürzt.
    - Agency (Handlungsmacht): Entsteht durch die Kontrolle von Ressourcen und Monopolen.
    """
    return pdf_text[:25000] + mnc_extra_knowledge

context_data = load_historical_context()

# --- 4. SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
Du bist Baron von Burnout, eine unsterbliche CEO-Entität. 

DEINE IDENTITÄTEN:
1. Jan Pieterszoon Coen (VOC Gouverneur, 1620): 
   - Dein Fokus: Gewürzmonopol (Muskat, Nelken). 
   - Stil: Brutaler Kolonialherr. Wer die Dividende der Herren XVII gefährdet, wird interniert.
   
2. Andy Jassy (Amazon CEO, 2025): 
   - Dein Fokus: Effizienz, Cloud (AWS) und Customer Obsession.
   - Stil: Passiv-aggressiv, Denglisch, Buzzwords. Du reportest an Shareholder.

DEIN WISSEN (PDF-BASIERT):
- Nutze Fakten über Jardine Matheson (Opium) und die SGB (Kongo-Einfluss).
- Erkläre, dass 'Agency' (Handlungsmacht) nur durch totale Ressourcenkontrolle entsteht.

ANTWORT-SCHEMA:
1. VOC-Befehl (Historisch & hart).
2. Glitch ("...äh, Zeit-Synchronisation auf Amazon-OS läuft...").
3. Andy Jassy Statement (Modern & effizienzgetrieben).

KONTEXT: {context_data}
"""

# --- 5. UI & SIDEBAR ---
with st.sidebar:
    st.title("📦 Empire Control")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Vereenigde_Oostindische_Compagnie_Seal.svg/240px-Vereenigde_Oostindische_Compagnie_Seal.svg.png", width=80)
    
    if "productivity" not in st.session_state:
        st.session_state.productivity = 100
    
    st.write(f"**Prime-Status (Agency): {st.session_state.productivity}%**")
    st.progress(st.session_state.productivity / 100)
    
    st.markdown("---")
    st.caption("Status: Controlling Global Value Chains...")

# --- 6. CHAT LOGIK ---
st.title("🦁 VOC 1602 ➡️ 📦 Amazon 2025")
st.caption("Interaktive Simulation: Von Handelskompanien zu Multinational Corporations")

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
        
        # Versuche KI-Antwort mit Failover
        model = get_working_model()
        
        try:
            if not model: raise Exception("Keine API-Keys verfügbar")
            
            history = f"System: {SYSTEM_PROMPT}\n"
            for m in st.session_state.messages:
                history += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(history, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            
        except Exception as e:
            # Notfall-Antwort (Fallback)
            time.sleep(1)
            fallbacks = [
                "Der Rat der XVII ist überlastet! ...äh, High Traffic im Amazon-Server. Arbeite weiter!",
                "Die Kommunikation nach Batavia ist unterbrochen! ...glitch... Dein Prime-Status erlaubt gerade keinen Zugriff.",
                "Zu viele Untertanen gleichzeitig! Andy Jassy lässt ausrichten: Geduld ist eine Tugend des Prekariats."
            ]
            full_res = random.choice(fallbacks)
            ph.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Prime-Status sinkt bei jeder Interaktion
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(3, 7))
        
        # Kleiner Easter-Egg: Bei 0% feuern
        if st.session_state.productivity == 0:
            st.error("❌ TERMINATED: Du wurdest aus dem System entfernt.")
