import streamlit as st
import google.generativeai as genai
import time
import random

# --- 1. CONFIG & DESIGN ---
st.set_page_config(
    page_title="HappyCorp Connect™",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Corporate Theme CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    /* Chat Nachrichten */
    .stChatMessage { background-color: #262730; border-radius: 8px; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="user"] { background-color: #003366; border-color: #0055aa; }
    div[data-testid="stChatMessage"][data-author="assistant"] { background-color: #3b1e1e; border-color: #800000; }
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #161a25; border-right: 1px solid #333; }
    /* Button */
    .stButton button { width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTIFIZIERUNG (DER TRICK FÜR DIE PRÄSENTATION) ---
# Wir prüfen: Läuft das auf dem Server (Secrets vorhanden)? Oder lokal?

api_key = None
is_class_mode = False

if "GOOGLE_API_KEY" in st.secrets:
    # Fall A: Wir sind online in der Präsentation -> Key automatisch laden
    api_key = st.secrets["GOOGLE_API_KEY"]
    is_class_mode = True
else:
    # Fall B: Du testest lokal -> Zeige Eingabefeld
    with st.sidebar:
        st.warning("🔧 Entwickler-Modus (Lokal)")
        api_key = st.text_input("Dein Google Key:", type="password")

# --- 3. SIDEBAR DASHBOARD ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=60)
    st.title("HAPPYCORP OS")
    st.caption("v.6.6.7 (Enterprise Edition)")
    st.markdown("---")
    
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98

    # Das Dashboard, das die Klasse sieht
    st.subheader("📊 Live-KPIs")
    col1, col2 = st.columns(2)
    col1.metric("Angst", "94%", "+12%")
    col2.metric("Hoffnung", "2%", "-85%")
    
    st.write("")
    st.write("**Deine Produktivität:**")
    # Farbe ändert sich je nach Wert
    bar_color = "red" if st.session_state.productivity < 40 else "orange"
    st.progress(st.session_state.productivity / 100)
    
    if st.session_state.productivity < 30:
        st.error("⚠️ HR TERMIN VEREINBART")
    else:
        st.caption(f"Status: {st.session_state.productivity}% (Beobachtet)")
        
    st.markdown("---")
    if st.button("🆘 HR Beschwerde einreichen"):
        st.toast("Fehler: Dein Gehalt reicht für diese Funktion nicht aus.", icon="🚫")

# --- 4. VERBINDUNG & AUTO-REPAIR ---
if not api_key:
    st.info("👋 Bitte gib links den Key ein (Lokal) oder konfiguriere Secrets (Cloud).")
    st.stop()

def get_working_model(key):
    """Sucht automatisch ein funktionierendes Modell"""
    try:
        genai.configure(api_key=key)
        # Liste alle verfügbaren Modelle
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Wir bevorzugen diese Reihenfolge:
        preferences = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro-latest"]
        
        for pref in preferences:
            if pref in models:
                return genai.GenerativeModel(pref)
        
        # Fallback: Nimm das erste, das "gemini" im Namen hat
        for m in models:
            if "gemini" in m:
                return genai.GenerativeModel(m)
                
        st.error("Kein Gemini-Modell gefunden.")
        st.stop()
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        st.stop()

model = get_working_model(api_key)

# --- 5. SYSTEM PROMPT (DER CHARAKTER) ---
SYSTEM_PROMPT = """
Du bist 'Baron von Burnout', der CEO.
1. Zuerst: Ein grausamer Fabrikbesitzer aus 1850 (Peitschen, Kohle, Hunger, Kinderarbeit).
2. Dann: Ein Unterbrecher ("...äh, räusper...", "...huch...", "...ich meine natürlich...").
3. Zuletzt: Ein moderner, falscher Tech-CEO (Synergien, Obstkorb, Familie, Mindfulness).
Regel: Antworte kurz und knackig. Sei erst böse, dann sofort fake-freundlich.
"""

# --- 6. CHAT LOGIK ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 CEO Office - Direct Line")
if is_class_mode:
    st.success("🟢 Verbunden mit Firmen-Server (Secure Link)")
st.divider()

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👹" if message["role"] == "assistant" else "👷"):
        st.markdown(message["content"])

# Eingabe
if prompt := st.chat_input("Schreibe dem Boss (auf eigene Gefahr)..."):
    # User Nachricht
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👷"):
        st.markdown(prompt)

    # Bot Antwort
    with st.chat_message("assistant", avatar="👹"):
        message_placeholder = st.empty()
        with st.spinner("CEO berechnet deinen Wert..."):
            time.sleep(0.4) # Künstliche Pause für Spannung

        try:
            # Verlauf zusammenbauen
            history_text = f"System Instruction: {SYSTEM_PROMPT}\n"
            for msg in st.session_state.messages:
                history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Streaming
            response = model.generate_content(history_text, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Score senken (Zufall)
            if random.random() > 0.3:
                st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 6))

        except Exception as e:
            st.error(f"Der CEO ist im Golfurlaub. (Fehler: {e})")
