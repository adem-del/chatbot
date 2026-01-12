import streamlit as st
import google.generativeai as genai
import time
import random
from PIL import Image
from pypdf import PdfReader # NEU: Für das PDF

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

def get_model(key):
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model(api_key)

# --- 3. DAS PDF LADEN (WISSENSDATENBANK) ---
def load_company_history():
    try:
        # Hier muss der exakte Name deiner Datei stehen!
        reader = PdfReader("Informations,history.pdf.pdf") 
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        return None

# Wir laden das PDF einmalig in den Speicher
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = load_company_history()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
    st.title("HAPPYCORP ARCHIVE")
    
    # Anzeige, ob das PDF geladen wurde
    if st.session_state.pdf_content:
        st.success("📚 Historisches Archiv: GELADEN")
        st.caption("Der CEO hat Zugriff auf 400 Jahre Firmengeschichte.")
    else:
        st.warning("⚠️ Archiv nicht gefunden (history.pdf fehlt)")

    st.markdown("---")
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    st.write("**Produktivität:**")
    st.progress(st.session_state.productivity / 100)

# --- 5. DER INTELLIGENTE SYSTEM PROMPT ---

# Hier passiert die Magie: Wir geben dem Bot das PDF als Kontext!
pdf_context = ""
if st.session_state.pdf_content:
    pdf_context = f"""
    HINTERGRUNDWISSEN (Nutz das für deine historische Persönlichkeit):
    {st.session_state.pdf_content[:30000]} 
    (Nutze Fakten über Handelskompanien, VOC, EIC, Monopole und Kolonialismus aus diesem Text, 
    um deine Grausamkeit historisch zu begründen.)
    """
    # Hinweis: [:30000] begrenzt den Text, falls das PDF riesig ist, 
    # aber Gemini Flash schafft locker ganze Bücher.

SYSTEM_PROMPT = f"""
Du bist 'Baron von Burnout', der CEO.
Deine gespaltene Persönlichkeit basiert auf der Evolution der Firma (siehe Hintergrundwissen):

1. **Das ID (Die Historie):** Du bist ein Gouverneur einer alten Handelskompanie (wie im PDF beschrieben). 
   - Zitiere Begriffe aus dem PDF wie "Oktroy", "Dividende", "Gewürzmonopol" oder historische Grausamkeiten.
   - Du siehst Angestellte als Eigentum der Kompanie.
   
2. **Das EGO (Die Moderne):** Du bist ein moderner CEO einer "Multinational Corporation".
   - Du übersetzt die alten Begriffe in modernes "Corporate Speak" (Global Value Chains, Stakeholder Value).

REGEL:
1. Beginne mit einem historischen Fakt/Befehl basierend auf dem PDF ("Wir brauchen mehr Gewürze aus den Kolonien!").
2. Unterbrich dich ("...äh, räusper...").
3. Übersetze es modern ("...wir müssen unsere Supply Chain optimieren.").

{pdf_context}
"""

# --- 6. CHAT LOGIK ---
st.title("💬 CEO Office (Powered by History)")
st.caption("Der Bot nutzt jetzt echtes historisches Wissen aus deinem PDF.")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👹" if msg["role"] == "assistant" else "👷"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage etwas zur Firmengeschichte..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👷"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👹"):
        message_placeholder = st.empty()
        
        try:
            # Kontext bauen
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
