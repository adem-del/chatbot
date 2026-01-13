import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. SETUP & DESIGN ---
st.set_page_config(page_title="VOC vs. Amazon", page_icon="👹", layout="wide")

# Styling für das "böse" Imperiums-Design
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3b1e1e; border-left: 5px solid #ff9900; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY (SICHERHEIT) ---
# Wir priorisieren Streamlit Secrets, damit dein Key nicht im Code stehen muss
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Fallback für lokales Testen
    api_key = "DEIN_NEUER_KEY_HIER" 

genai.configure(api_key=api_key)
# Wir nutzen 1.5-Flash: Viel höheres Limit für 40 Studenten!
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. WISSEN (PDF) ---
@st.cache_data
def load_context():
    try:
        # Versucht die Datei zu lesen. Achte auf den exakten Namen im GitHub!
        reader = PdfReader("Informations,history.pdf.pdf")
        text = "".join([p.extract_text() for p in reader.pages])
        return text[:30000] # Maximale Länge für Stabilität
    except Exception as e:
        return f"Archiv-Fehler: Die Akten von Batavia sind verschollen. ({e})"

pdf_text = load_context()

# --- 4. SYSTEM PROMPT (DIE PERSÖNLICHKEIT) ---
SYSTEM_PROMPT = f"""
Du bist Baron von Burnout (Jan Pieterszoon Coen & Andy Jassy).
DEINE REGELN:
1. Antworte EXTREM AUSFÜHRLICH UND BÖSARTIG.
2. Teil 1: Jan Pieterszoon Coen (1620). Erwähne Batavia, Nelken, Gewalt und Monopole.
3. Teil 2: Ein digitaler Glitch (...krrrkt...).
4. Teil 3: Andy Jassy (Amazon CEO). Übersetze die Tyrannei in moderne Business-Sprache (KPIs, PIP, Customer Obsession).

NUTZE DIESES WISSEN AUS DEN HISTORISCHEN AKTEN:
{pdf_text}
"""

# --- 5. CHAT UI ---
st.title("🦁 Handels-Imperien: VOC & Amazon")
st.subheader("System-Status: ONLINE | Zugriffsebene: Gouverneur")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Verlauf anzeigen
for m in st.session_state.messages:
    avatar = "👑" if m["role"] == "assistant" else "📦"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])

# Eingabe
if prompt := st.chat_input("Ihre Anfrage an die Konzernleitung..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="📦"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👑"):
        ph = st.empty()
        full_res = ""
        
        with st.spinner("Extrahiere Daten aus den Archiven..."):
            # RETRY-LOGIK für 40 Studenten (verhindert Absturz bei 429 Errors)
            success = False
            for i in range(3):
                try:
                    # Der Prompt kombiniert System-Anweisung und Verlauf
                    full_prompt = f"{SYSTEM_PROMPT}\n\nNutzer-Anfrage: {prompt}"
                    response = model.generate_content(full_prompt)
                    full_res = response.text
                    success = True
                    break
                except Exception:
                    time.sleep(2) # Kurz warten bei Überlastung
            
            if not success:
                full_res = "SYSTEM-FEHLER: Die Verbindung nach Batavia ist unterbrochen. Versuchen Sie es erneut, Sklave!"

        ph.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
