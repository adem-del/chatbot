import streamlit as st
import google.generativeai as genai
import time
import random
from pypdf import PdfReader

# --- 1. SETUP ---
st.set_page_config(page_title="VOC vs. Amazon", page_icon="👹", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #262730; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="assistant"] { 
        background-color: #3b1e1e; border-left: 5px solid #ff9900; 
    }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY ---
# FÜGE HIER DEINEN NEUEN, FUNKTIONIERENDEN KEY EIN (in die Anführungszeichen)
# WICHTIG: Nach dem Einfügen auf Streamlit Cloud "Reboot App" klicken!
MY_API_KEY = "DEIN_NEUER_KEY_HIER"

def get_model():
    try:
        genai.configure(api_key=MY_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

# --- 3. DIE LANGEN NOTFALL-ANTWORTEN (FALLBACK) ---
# Diese Texte kommen, wenn der Key nicht geht. Sie sind jetzt EXTREM LANG.
LONG_FALLBACKS = [
    """(VOC): Schweig, du unwürdiger Wurm! Glaubst du, die Herren XVII in Amsterdam bezahlen uns für Faulheit? Die Speicher in Batavia sind leer, und die Flotte wartet auf Muskatnuss! Wenn du nicht sofort an die Arbeit gehst, lasse ich dich kielholen und deine Ration auf verschimmeltem Zwieback kürzen! Wir haben ein Monopol zu verteidigen, und ich dulde keinen Widerstand!
    
...*krrrrk*... *Zeit-Synchronisation*... *Update auf Corporate-OS*...
    
(Amazon): Andy Jassy hier. Wir haben gerade deine Produktivitätsdaten analysiert und festgestellt, dass deine 'Time-Off-Task' Werte extrem hoch sind. Das entspricht nicht unserer 'Customer Obsession'. Bei Amazon erwarten wir, dass du jede Sekunde nutzt, um die Supply Chain zu optimieren. Wir setzen dich hiermit auf einen 'Performance Improvement Plan'. Arbeite härter, oder dein Account wird deaktiviert. (System: Offline-Modus aktiv)""",

    """(VOC): Bei meiner Ehre als Generalgouverneur! Die Banda-Inseln haben sich unterworfen, und du wagst es, mir zu widersprechen? Wir haben diese Handelsrouten mit Blut und Eisen gesichert! Opium, Gewürze, Tee – alles muss fließen, damit die Dividende stimmt. Wer den Handel stört, ist ein Feind der Kompanie und wird ohne Gnade eliminiert! An die Ruder mit dir!
    
...*bzzzt*... *Daten-Glitch*... *Lade Amazon Leadership Principles*...
    
(Amazon): Das war... unproduktiv. Hier ist das Management. Wir sehen, dass du versuchst, das System zu hinterfragen. Das ist nicht 'Day 1 Mentality'. Wir müssen skalieren, und dafür brauchen wir bedingungslosen Einsatz. Deine Pausen wurden soeben vom Algorithmus gestrichen, um die Effizienz im Fulfillment Center zu steigern. Zurück an die Arbeit, bevor der Roboter deinen Job übernimmt. (System: Offline-Modus aktiv)"""
]

# --- 4. WISSEN (PDF) ---
@st.cache_data
def load_context():
    try:
        reader = PdfReader("Informations,history.pdf.pdf")
        text = "".join([p.extract_text() for p in reader.pages[:25]])
        return text[:25000]
    except:
        return "Archiv nicht verfügbar."

pdf_text = load_context()

# --- 5. SYSTEM PROMPT (BEFEHL: LANGE ANTWORTEN) ---
SYSTEM_PROMPT = f"""
Du bist Baron von Burnout (Jan Pieterszoon Coen & Andy Jassy).
Deine oberste Regel: **ANTWORTE LANG UND AUSFÜHRLICH!**

ROLLEN:
1. Jan Pieterszoon Coen (1620): Halte eine lange, wütende Strafpredigt. Erwähne Banda, Batavia, Gewürze, Monopole und Gewalt. Sei nicht kurz angebunden!
2. Andy Jassy (2025): Übersetze das in lange, komplizierte Corporate-Sätze. Nutze viele Buzzwords (KPI, Deep Dive, Deliver Results).

STRUKTUR:
- Mindestens 4-5 Sätze als VOC-Gouverneur.
- Kurzer Glitch.
- Mindestens 4-5 Sätze als Amazon-Manager.

WISSEN:
Nutze Fakten aus dem Text: {pdf_text[:10000]}
"""

# --- 6. CHAT ---
st.title("Handels-Imperien (Long Version)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="👑" if m["role"] == "assistant" else "📦"):
        st.markdown(m["content"])

if prompt := st.chat_input("Deine Nachricht..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="📦"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👑"):
        ph = st.empty()
        full_res = ""
        
        try:
            # 1. Versuch: Echte KI (Google)
            model = get_model()
            if not model: raise Exception("Key Config Error")
            
            history = f"System: {SYSTEM_PROMPT}\n"
            for m in st.session_state.messages[-3:]:
                history += f"{m['role']}: {m['content']}\n"
            
            response = model.generate_content(history, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            
            # Falls Google leer antwortet, werfen wir Fehler, um Fallback zu nutzen
            if len(full_res) < 5: raise Exception("Empty Response")
            
            ph.markdown(full_res)

        except Exception as e:
            # 2. Versuch: Wenn Key kaputt ist -> LANGE Fallback-Antwort nutzen
            time.sleep(1)
            full_res = random.choice(LONG_FALLBACKS)
            ph.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
