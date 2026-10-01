import os
from typing import Annotated

import voyageai
from langchain_core.tools import tool
from langchain_groq import ChatGroq  # Remplacement de ChatOpenAI par ChatGroq
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pymongo import MongoClient
from typing_extensions import TypedDict

# --- 1. Initialisation MongoDB ---
def init_mongodb(mongodb_uri: str | None = None):
    """Initialise le client MongoDB et récupère les collections."""
    mongodb_client = MongoClient(mongodb_uri or os.environ["MONGODB_URI"])
    DB_NAME = "ai_agents"
    vs_collection = mongodb_client[DB_NAME]["chunked_docs"]
    full_collection = mongodb_client[DB_NAME]["full_docs"]
    return mongodb_client, vs_collection, full_collection

# --- 2. Fonction d'assistance pour les Embeddings (Voyage AI) ---
def generate_embedding(text: str, voyage_api_key: str | None = None) -> list[float]:
    """Génère un vecteur d'embedding pour la recherche sémantique."""
    vo = voyageai.Client(api_key=voyage_api_key or os.environ["VOYAGE_API_KEY"])
    result = vo.embed([text], model="voyage-3-lite", input_type="query")
    return result.embeddings[0]

# --- 3. Définition des Outils (`@tool`) ---
def create_tools(vs_collection, full_collection, voyage_api_key: str):
    @tool
    def get_information_for_question_answering(query: str) -> str:
        """Recherche des informations pertinentes dans la documentation MongoDB découpée."""
        query_embedding = generate_embedding(query, voyage_api_key)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 50,
                    "limit": 5
                }
            },
            {"$project": {"body": 1, "_id": 0}}
        ]
        results = list(vs_collection.aggregate(pipeline))
        return "\n".join(doc.get("body", "") for doc in results)

    @tool
    def get_page_content_for_summarization(title: str) -> str:
        """Récupère une page de documentation complète par son titre exact pour la résumer."""
        doc = full_collection.find_one({"title": title}, {"body": 1, "_id": 0})
        if doc:
            return doc.get("body", "Document trouvé mais vide.")
        return "Aucune page trouvée avec ce titre exact."

    return [get_information_for_question_answering, get_page_content_for_summarization]

# --- 4. Configuration de l'État et du Graphe (LangGraph) ---
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

def create_agent_workflow(llm, tools_list):
    llm_with_tools = llm.bind_tools(tools_list)
    
    def agent_node(state: GraphState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def route_tools(state: GraphState):
        """Détermine s'il faut appeler un outil ou terminer."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(GraphState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools_list))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", route_tools, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")  # Boucle de rétroaction
    
    return workflow

# --- 5. Fonction Principale (`main`) ---
def build_agent_app(
    mongodb_uri: str | None = None,
    groq_api_key: str | None = None,
    voyage_api_key: str | None = None,
):
    """Construit l'agent et son checkpoint MongoDB pour les interfaces."""
    mongodb_uri = mongodb_uri or os.environ.get("MONGODB_URI")
    groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
    voyage_api_key = voyage_api_key or os.environ.get("VOYAGE_API_KEY")
    missing = [
        name for name, value in (
            ("MONGODB_URI", mongodb_uri),
            ("GROQ_API_KEY", groq_api_key),
            ("VOYAGE_API_KEY", voyage_api_key),
        ) if not value
    ]
    if missing:
        raise ValueError("Clés manquantes : " + ", ".join(missing))

    mongodb_client, vs_collection, full_collection = init_mongodb(mongodb_uri)
    llm = ChatGroq(
        api_key=groq_api_key,
        model_name="openai/gpt-oss-20b",
        temperature=0
    )
    workflow = create_agent_workflow(
        llm,
        create_tools(vs_collection, full_collection, voyage_api_key)
    )
    checkpointer = MongoDBSaver(mongodb_client)
    return workflow.compile(checkpointer=checkpointer)


def main():
    app = build_agent_app()

    # Session ID unique pour tester la mémoire
    config = {"configurable": {"thread_id": "session_groq_01"}}

    # --- Tour 1 : Question technique ---
    print("--- Tour 1 ---")
    input_message = {"messages": [("user", "Quelles sont les bonnes pratiques pour les sauvegardes MongoDB ?")]}

    for event in app.stream(input_message, config, stream_mode="values"):
        latest_msg = event["messages"][-1]
        latest_msg.pretty_print()

    # --- Tour 2 : Test de la mémoire ---
    print("\n--- Tour 2 (Test de mémoire) ---")
    follow_up_message = {"messages": [("user", "Peux-tu me rappeler quelle était ma première question ?")]}

    for event in app.stream(follow_up_message, config, stream_mode="values"):
        latest_msg = event["messages"][-1]
        latest_msg.pretty_print()

if __name__ == "__main__":
    main()