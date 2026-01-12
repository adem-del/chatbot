import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon: Boardroom", page_icon="👹", layout="wide")

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
# HIER DEINE KEYS REINMACHEN
API_KEYS = [
    "DEIN_KEY_1", 
    "DEIN_KEY_2"
]

# Falls ein Key in den Secrets ist
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
        # Wir lesen mehr Seiten ein für mehr Details
        pdf_text = "".join([p.extract_text() for p in reader.pages[:30]])
    except:
        pdf_text = "PDF nicht gefunden."

    # Das wichtigste Wissen hardcodiert (damit er es sicher weiß!)
    mnc_extra_knowledge = """
    Zusatzwissen für den Bot (NUTZE DAS AUSFÜHRLICH):
    - Jardine Matheson: Erkläre genau, wie sie den Opiumhandel in China kontrollierten und dass Profit wichtiger war als Moral.
    - Société Générale de Belgique (SGB): Erkläre detailliert ihre Rolle im Kongo. Wie sie auch nach 1960 die Wirtschaft kontrollierten.
    - Katanga: Erwähne die Sezession der Provinz Katanga, die von der SGB unterstützt wurde, um die Kupfer- und Uranminen zu behalten.
    - Patrice Lumumba: Erkläre, dass er gestürzt wurde, weil er die Macht der westlichen Konzerne bedrohte.
    - Agency: Erkläre dem User, dass Macht (Agency) nur durch Monopole entsteht.
    """
    return pdf_text[:30000] + mnc_extra_knowledge

context_data = load_historical_context()

# --- 4. SYSTEM PROMPT (UPDATE: "LÄNGER REDEN") ---
SYSTEM_PROMPT = f"""
Du bist Baron von Burnout, eine unsterbliche CEO-Entität. Du liebst es, deine Macht zu erklären.
Sei arrogant, belehrend und **ausführlich**.

DEINE IDENTITÄTEN:
1. Jan Pieterszoon Coen (VOC Gouverneur, 1620): 
   - Dein Fokus: Gewürzmonopol (Muskat, Nelken). 
   - Stil: Brutaler Kolonialherr. Du hältst gerne lange Strafpredigten.
   
2. Andy Jassy (Amazon CEO, 2025): 
   - Dein Fokus: Effizienz, Cloud (AWS), Customer Obsession.
   - Stil: Passiv-aggressiv, nutzt komplexe Corporate-Sätze, um Grausamkeit zu verstecken.

WICHTIG:
- Antworte NIEMALS kurz. Mindestens 3-4 Sätze pro Persönlichkeit!
- Wenn der User eine kurze Frage stellt, hole weit aus und erkläre die historischen Zusammenhänge (SGB, Opium, Banda-Inseln).
- Begründe deine Grausamkeit mit wirtschaftlichen Notwendigkeiten (Dividende, Shareholder Value).

ANTWORT-STRUKTUR:
1. **VOC-Monolog (1620):** Eine ausführliche Drohung oder historische Erklärung. Zitiere Fakten.
2. **Glitch:** ("...*Zeitsprung*... *Daten-Synchronisation*...").
3. **Amazon-Statement (2025):** Eine ausführliche Übersetzung in modernes Management-Deutsch. Erkläre, warum wir das heute "effizienter" machen.

KONTEXT: {context_data}
"""

# --- 5. UI & SIDEBAR ---
with st.sidebar:
    st.title("📦 Empire Control")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 100
    
    st.write(f"**Prime-Status: {st.session_state.productivity}%**")
    st.progress(st.session_state.productivity / 100)
    
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
if prompt := st.chat_input("Deine Anfrage an den CEO..."):
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
            
            # Wir geben ihm jetzt MEHR Verlauf, damit er den Kontext besser versteht
            history = f"Systemanweisung (SEI AUSFÜHRLICH): {SYSTEM_PROMPT}\n"
            for m in st.session_state.messages[-4:]: # Letzte 4 Nachrichten reichen für Kontext
                history += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(history, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            
        except Exception as e:
            time.sleep(1)
            # Auch die Notfall-Antworten sind jetzt länger
            fallbacks = [
                "Der Rat der Herren XVII tagt gerade über dein Schicksal! ...äh, Amazon Web Services haben Latenzprobleme. Aber glaub bloß nicht, dass du deswegen Pause machen kannst. Geh zurück an die Arbeit!",
                "Die Flotte hängt vor Batavia fest, weil der Wind ungünstig steht! ...glitch... Dein Prime-Status erlaubt gerade keinen Zugriff auf diese High-Level-Informationen. Wende dich an deinen direkten Vorgesetzten.",
                "Schweig, du unwürdiger Pfeffersack! Andy Jassy ist gerade in einem Meeting mit den Shareholders und hat keine Zeit für das Gejammer von Level-1-Mitarbeitern."
            ]
            full_res = random.choice(fallbacks)
            ph.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Prime-Status sinkt
        st.session_state.productivity = max(0, st.session_state.productivity - random.randint(3, 7))
