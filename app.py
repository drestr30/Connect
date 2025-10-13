import streamlit as st
import requests
import logging
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:7071/api")
TOKEN = os.getenv("TOKEN", None)

logging.basicConfig(level=logging.INFO)

st.title("🎴Connect")

dynamics_response = requests.get(f"{BASE_URL}/get_dynamics" + f'?code={TOKEN}' if TOKEN else '')
dynamics = dynamics_response.json() if dynamics_response.status_code == 200 else [{"name": "questions"}]
logging.info(f"Dynamics response: {dynamics_response.status_code}, {dynamics_response.text}")

# Sidebar with questions (hidable by default in Streamlit)
with st.sidebar:
    st.header("⚙️ Configuración de Sesión") 
    entorno = st.radio("¿En qué entorno estás?", ["family", "friends", "couple"])
    accion = st.radio("¿Qué quieres hacer?", ["fun", "meet"])
    intimidad = st.selectbox("Nivel de intimidad", ["1", "2", "3", "4"])
    hot = st.checkbox("¿Quieres preguntas picantes?", value=False)
    drink = st.checkbox("¿Quieres preguntas para beber?", value=False)
    dinamica = st.selectbox("Dinámica", [dynamic["name"] for dynamic in dynamics])

    if st.button("Iniciar Sesión"):
        selections = {
            "social_context": entorno,
            "purpose": accion,
            "tone": intimidad,
            "dynamic": dinamica,
            "hot": hot,
            "drink": drink
        }
    
        logging.info(f"User selections: {selections}")

        try:
            # Create session
            session_url = f"{BASE_URL}/create_session" + f'?code={TOKEN}' if TOKEN else ''
            response = requests.post(
                session_url,
                json={"selections": selections}
            )
            response.raise_for_status()
            st.session_state.session_id = response.json()#.get("session_id")

            # Get cards
            cards_url = f"{BASE_URL}/get_cards/{st.session_state.session_id.get('session_id')}" + f'?code={TOKEN}' if TOKEN else ''
            cards_response = requests.get(cards_url)
            cards_response.raise_for_status()
            st.session_state.cards = cards_response.json()
            st.session_state.current_index = 0

            st.success("✅ Sesión creada")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error en la solicitud: {e}")

# Initialize session state if not set
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "cards" not in st.session_state:
    st.session_state.cards = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# Main page: show cards one by one
if st.session_state.cards:
    card = st.session_state.cards[st.session_state.current_index]
    st.subheader(f"🃏 Card {st.session_state.current_index + 1}")
    st.json(card)  # display raw card JSON (can be replaced with pretty formatting)
    status_url = f"{BASE_URL}/update_card_status" + f'?code={TOKEN}' if TOKEN else ''
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅ Anterior", key=f"prev_{st.session_state.current_index}"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
            else:
                st.info("🎉 No hay más cartas")
    with col2:
        if st.button("👍 Me gusta", key=f"like_{st.session_state.current_index}"):
            try:
                requests.post(
                    status_url,
                    json={
                        "session_id": st.session_state.session_id.get('session_id'),
                        "card_id": card.get("id"),
                        "liked": True
                    }
                )
                st.success("❤️ Carta marcada como favorita")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error al enviar like: {e}")
            
            if st.session_state.current_index < len(st.session_state.cards) - 1:
                st.session_state.current_index += 1
                st.rerun()
            else:
                st.info("🎉 No hay más cartas")

    with col3:
        if st.button("➡️ Siguiente", key=f"next_{st.session_state.current_index}"):
            try:
                requests.post(
                    status_url,
                    json={
                        "session_id": st.session_state.session_id.get('session_id'),
                        "card_id": card.get("id"),
                        "liked": False
                    }
                )
                st.info("Carta marcada como vista")
            except requests.exceptions.RequestException as e:
                st.error(f"Error al marcar carta como vista: {e}")

            if st.session_state.current_index < len(st.session_state.cards) - 1:
                st.session_state.current_index += 1
                st.rerun()
            else:
                st.info("🎉 No hay más cartas")
            
        
# Show session ID at the bottom
if st.session_state.session_id:
    st.divider()
    st.caption(f"🔑 ID de Sesión: {st.session_state.session_id.get('session_id')}")
    cards_list = "\n- ".join([card['card_data'] for card in st.session_state.cards])
    st.caption(f"📝 Session cards:\n- {cards_list}")
    st.divider()
    display_prompt = st.session_state.session_id.get('system_message').replace('#', '') + "\n\n" + st.session_state.session_id.get('user_message').replace('#', '')
    st.caption(f"💬Full prompt:")
    st.caption(display_prompt)
