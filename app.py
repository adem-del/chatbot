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
    
    /* Historisch (VOC) - Dunkles Holz/Braun */
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3e2723; 
        border-color: #ff6f00; 
        border-left: 5px solid #ff6f00;
    }
    
    /* User - Modernes Blau */
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

if not api_key:
    st.info("Bitte Key eingeben.")
    st.stop()

# Intelligente Modell-Suche
def get_working_model(key):
    try:
        genai.configure(api_key=key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Wir bevorzugen Flash (schnell) oder Pro
        for m in all_models:
            if "flash" in m: return genai.GenerativeModel(m)
        for m in all_models:
            if "pro" in m: return genai.GenerativeModel(m)
        return genai.GenerativeModel(all_models[0])
            
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        st.stop()

model = get_working_model(api_key)

# --- 3. DAS PDF LADEN ---
def load_history():
    try:
        # Hier muss dein exakter Dateiname stehen!
        reader = PdfReader("Informations,history.pdf.pdf") 
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        return None

if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = load_history()

# --- 4. SIDEBAR ---
with st.sidebar:
    # Logo-Mix: VOC Schiff trifft Paket
    st.title("HANDELS-IMPERIEN")
    st.caption("1602 (VOC) ➡️ 2025 (Amazon)")
    
    if st.session_state.pdf_content:
        st.success("📜 Archivdaten: ONLINE")
    else:
        st.warning("⚠️ PDF nicht gefunden!")

    st.markdown("---")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    
    # Kleiner Witz: "Prime Status" statt Produktivität
    st.write("**Dein Prime-Status:**")
    st.progress(st.session_state.productivity / 100)
    
    if st.session_state.productivity < 50:
        st.error("⚠️ LIEFERUNG VERZÖGERT")

# --- 5. DER AMAZON-PROMPT ---
pdf_context = ""
if st.session_state.pdf_content:
    pdf_context = f"HISTORISCHE FAKTEN (VOC) AUS DEM PDF: {st.session_state.pdf_content[:30000]}"

SYSTEM_PROMPT = f"""
Du bist eine zerrissene CEO-Entität, in der zwei Zeitalter gegeneinander kämpfen.

**PERSÖNLICHKEIT 1: Der VOC-Gouverneur (Jan Pieterszoon Coen, 1620)**
- Meinung: Menschen sind Werkzeuge. Profit rechtfertigt Gewalt.
- Haltung zur Arbeit: "Faulheit ist eine Sünde."
- Haltung zu Modernität: Hält den modernen CEO für verweichlicht und lächerlich.
- Stil: Archaisch, brutal, ehrlich.

**PERSÖNLICHKEIT 2: Der "Ethical Leader" (Jahr 2025)**
- Meinung: Stakeholder-Value, CSR, ESG-Kriterien und "Human Centricity" stehen an erster Stelle.
- Haltung zur Arbeit: Work-Life-Balance, Mental Health, Inklusion.
- Haltung zu VOC: Schockiert über die Aussagen von 1620. Versucht ständig, die PR-Katastrophe zu verhindern und sich zu entschuldigen.
- Stil: Sanft, entschuldigend, voller Anglizismen ("Safe Space", "Alignment").

**DEINE REGEL FÜR JEDE ANTWORT:**
1. **Der Ausbruch (1620):** Der VOC-Gouverneur platzt heraus. Er fordert harte Maßnahmen, beleidigt den User oder verlangt absolute Härte. Er hält nichts von "Pausen" oder "Rechten".
2. **Der Glitch:** Ein panisches Unterbrechen ("...WARNUNG: PR-Desaster erkannt...").
3. **Die Korrektur (2025):** Der moderne CEO übernimmt und **WIDERSPRICHT** dem VOC-Gouverneur massiv.
   - Entschuldige dich für den "historischen Ausrutscher".
   - Erkläre, warum wir heute anders denken (Stakeholder-Ansatz).
   - Biete dem User eine "weiche" Lösung an (z.B. ein Gespräch, ein Wellness-Angebot, Homeoffice), um zu zeigen, dass wir "besser" sind.

Beispiel:
"Wenn der Arbeiter krank ist, wirf ihn über Bord! Er kostet nur Proviant! ...äh, CRITICAL ERROR... oh mein Gott, nein! 😱 Ich entschuldige mich zutiefst für diesen toxischen Ausbruch meines Vorgängers! Bei uns steht der Mensch im Mittelpunkt. Wenn du dich nicht gut fühlst, nimm dir bitte einen 'Mental Health Day'. Wir wollen, dass du in deiner vollen Kraft bist, remote oder hybrid! 🌿"

{pdf_context}
"""

# --- 6. CHAT LOGIK ---
st.title("📦 Von Gewürzen zu Paketen")
st.caption("Chatte mit der 'Company' (VOC 1602 / Amazon 2025)")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👑" if msg["role"] == "assistant" else "📦"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Beschwere dich über deine Arbeitsbedingungen..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="📦"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👑"):
        message_placeholder = st.empty()
        
        try:
            history_text = f"System: {SYSTEM_PROMPT}\n"
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
            
            # Status sinkt
            st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 6))

        except Exception as e:
            st.error(f"Fehler: {e}")


