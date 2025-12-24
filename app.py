import streamlit as st
import google.generativeai as genai
import time
import random

# --- 1. SEITEN-CONFIG & DESIGN ---
st.set_page_config(
    page_title="HappyCorp Connect™",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PROFESSIONAL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stChatMessage { background-color: #262730; border-radius: 10px; padding: 10px; border: 1px solid #444; }
    div[data-testid="stChatMessage"][data-author="user"] { background-color: #004a77; border: 1px solid #0077b6; }
    div[data-testid="stChatMessage"][data-author="assistant"] { background-color: #3b1e1e; border: 1px solid #7f1d1d; }
    section[data-testid="stSidebar"] { background-color: #111; border-right: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=50)
    st.title("HAPPYCORP OS")
    st.caption("v.6.6.7 (Auto-Repair Build)")
    
    # API Key Feld
    api_key = st.text_input("🔑 Google API Key", type="password")
    st.caption("[Key hier gratis holen](https://aistudio.google.com/app/apikey)")
    
    st.markdown("---")
    
    # Dashboard
    if "productivity" not in st.session_state:
        st.session_state.productivity = 98
    
    st.write("**Deine Produktivität:**")
    st.progress(st.session_state.productivity / 100)
    st.caption(f"Status: {st.session_state.productivity}%")

# --- 4. VERBINDUNG & AUTO-MODELL-SUCHE ---
if not api_key:
    st.info("👋 Bitte logge dich links mit deinem Google API Key ein.")
    st.stop()

# Funktion, die automatisch ein funktionierendes Modell sucht
def get_working_model(key):
    genai.configure(api_key=key)
    
    # Wir suchen nach Modellen, die Text generieren können
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Bevorzugte Reihenfolge
        priority_list = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro-latest"]
        
        selected_model_name = None
        
        # 1. Prüfen ob ein Favorit da ist
        for priority in priority_list:
            if priority in available_models:
                selected_model_name = priority
                break
        
        # 2. Wenn nicht, nimm irgendein Gemini Modell
        if not selected_model_name:
            for m in available_models:
                if "gemini" in m:
                    selected_model_name = m
                    break
        
        # 3. Notfall: Nimm einfach das erste der Liste
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]

        if selected_model_name:
            # print(f"Benutze Modell: {selected_model_name}") # Für Debugging
            return genai.GenerativeModel(selected_model_name)
        else:
            st.error("Kein passendes Modell gefunden. Prüfe deinen API Key.")
            st.stop()
            
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        st.stop()

# Modell initialisieren (ruft die Such-Funktion auf)
model = get_working_model(api_key)

# --- 5. SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist 'Baron von Burnout', der CEO.
1. Zuerst: Ein grausamer Fabrikbesitzer aus 1850 (Peitschen, Kohle, Hunger).
2. Dann: Ein Unterbrecher ("...äh, räusper...", "...huch...").
3. Zuletzt: Ein moderner, falscher Tech-CEO (Synergien, Obstkorb, Familie).
Regel: Antworte kurz. Sei böse, dann falsch-freundlich.
"""

# --- 6. CHAT LOGIK ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 CEO Office")
st.divider()

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👹" if message["role"] == "assistant" else "👷"):
        st.markdown(message["content"])

# Eingabe
if prompt := st.chat_input("Nachricht an den Boss..."):
    # User Nachricht
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👷"):
        st.markdown(prompt)

    # Bot Antwort
    with st.chat_message("assistant", avatar="👹"):
        message_placeholder = st.empty()
        with st.spinner("CEO denkt nach..."):
            time.sleep(0.5)

        try:
            # Kontext bauen
            history_text = f"System Instruction: {SYSTEM_PROMPT}\n"
            for msg in st.session_state.messages:
                history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Generieren
            response = model.generate_content(history_text, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Score senken
            st.session_state.productivity = max(0, st.session_state.productivity - random.randint(2, 5))

        except Exception as e:
            st.error(f"Fehler: {e}")