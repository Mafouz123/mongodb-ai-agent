import uuid

import streamlit as st
import voyageai
from groq import Groq
from pymongo import MongoClient


st.set_page_config(page_title="MongoDB AI Agent", page_icon="M", layout="centered")
st.title("MongoDB AI Agent")
st.caption("Assistant de documentation MongoDB")

def validate_credentials(mongodb_uri: str, groq_api_key: str, voyage_api_key: str):
    results = {}
    client = None
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        results["MongoDB"] = "OK"
    except Exception as exc:
        results["MongoDB"] = f"Échec ({type(exc).__name__})"
    finally:
        if client is not None:
            client.close()

    try:
        Groq(api_key=groq_api_key).models.list()
        results["Groq"] = "OK"
    except Exception as exc:
        results["Groq"] = f"Échec ({type(exc).__name__})"

    try:
        voyageai.Client(api_key=voyage_api_key).embed(
            ["test de connexion"], model="voyage-3-lite", input_type="query"
        )
        results["Voyage AI"] = "OK"
    except Exception as exc:
        results["Voyage AI"] = f"Échec ({type(exc).__name__})"

    return results

with st.sidebar:
    st.subheader("Connexion")
    with st.form("credentials_form"):
        mongodb_uri = st.text_input("URI MongoDB", type="password")
        groq_api_key = st.text_input("Clé API Groq", type="password")
        voyage_api_key = st.text_input("Clé API Voyage AI", type="password")
        validate_button = st.form_submit_button("Vérifier les clés", type="primary")
    st.caption("Les clés restent en mémoire pour cette session et ne sont pas enregistrées sur disque.")

if validate_button:
    st.session_state.pop("credentials", None)
    st.session_state.pop("agent", None)
    if not all((mongodb_uri, groq_api_key, voyage_api_key)):
        st.session_state.credential_results = {"Configuration": "Renseignez les trois champs."}
    else:
        with st.spinner("Vérification des accès…"):
            results = validate_credentials(mongodb_uri, groq_api_key, voyage_api_key)
        st.session_state.credential_results = results
        if all(result == "OK" for result in results.values()):
            st.session_state.credentials = {
                "mongodb_uri": mongodb_uri,
                "groq_api_key": groq_api_key,
                "voyage_api_key": voyage_api_key,
            }
            st.session_state.pop("agent", None)
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())

for service, result in st.session_state.get("credential_results", {}).items():
    st.sidebar.write(f"{service} : {result}")

if "credentials" not in st.session_state:
    st.info("Saisissez vos clés dans le panneau Connexion pour démarrer le test.")
    st.stop()

from main import build_agent_app

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("Nouvelle conversation", icon=":material/refresh:"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Posez une question sur MongoDB")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_area = st.empty()
        try:
            if "agent" not in st.session_state:
                st.session_state.agent = build_agent_app(**st.session_state.credentials)
            agent = st.session_state.agent
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = agent.invoke({"messages": [("user", prompt)]}, config)
            answer = str(result["messages"][-1].content)
            response_area.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as exc:
            st.error(f"Échec de la requête ({type(exc).__name__}). Vérifiez la configuration et les services.")