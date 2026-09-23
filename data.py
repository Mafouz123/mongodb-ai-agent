import time

import voyageai
from datasets import load_dataset
from pymongo import MongoClient
from voyageai.error import RateLimitError

import key_param


def embed_texts_with_backoff(vo, texts, model="voyage-3-lite", max_retries=6):
    """Génère des embeddings avec stratégie de retry en cas de rate limiting."""
    if not texts:
        return []

    for attempt in range(max_retries):
        try:
            result = vo.embed(texts, model=model, input_type="document")
            return result.embeddings
        except RateLimitError as exc:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    "Quota Voyage AI dépassé. Ajoute un moyen de paiement dans le dashboard Voyage AI "
                    "ou réduis le volume d'upload/les batchs."
                ) from exc

            wait_time = 5 * (2**attempt)
            print(
                f"⏳ Limite de débit Voyage AI atteinte. Nouvelle tentative dans {wait_time}s "
                f"({attempt + 1}/{max_retries})..."
            )
            time.sleep(wait_time)


def load_and_populate_data():
    print("🚀 Chargement des jeux de données depuis Hugging Face...")
    full_docs_dataset = load_dataset("MongoDB/mongodb-docs", split="train")
    chunked_docs_dataset = load_dataset("MongoDB/mongodb-docs-embedded", split="train")

    print("🔌 Connexion à MongoDB Atlas...")
    mongodb_client = MongoClient(key_param.mongodb_uri)

    DB_NAME = "ai_agents"
    full_collection_name = "full_docs"
    chunked_collection_name = "chunked_docs"

    full_collection = mongodb_client[DB_NAME][full_collection_name]
    chunked_collection = mongodb_client[DB_NAME][chunked_collection_name]

    full_collection.delete_many({})
    chunked_collection.delete_many({})

    print("📥 Insertion des documents complets (full_docs)...")
    full_docs_list = list(full_docs_dataset)
    if full_docs_list:
        full_collection.insert_many(full_docs_list)
    print(f"✅ {len(full_docs_list)} documents complets insérés.")

    print("⚙️ Génération des embeddings et insertion des chunks (chunked_docs)...")
    vo = voyageai.Client(api_key=key_param.voyage_api_key)

    chunked_docs_list = list(chunked_docs_dataset)
    if not chunked_docs_list:
        print("Aucun document chunké à traiter.")
        return

    batch_size = 25
    for i in range(0, len(chunked_docs_list), batch_size):
        batch = chunked_docs_list[i:i + batch_size]
        texts = [doc.get("body", "") for doc in batch]

        embeddings = embed_texts_with_backoff(vo, texts, model="voyage-3-lite")

        for doc, embedding in zip(batch, embeddings):
            doc["embedding"] = embedding

        chunked_collection.insert_many(batch)
        print(
            f"   -> Batch {i // batch_size + 1} traité "
            f"({min(i + batch_size, len(chunked_docs_list))}/{len(chunked_docs_list)})"
        )

    print("🎉 Données chargées et indexées avec succès dans MongoDB !")

if __name__ == "__main__":
    load_and_populate_data()