# MongoDB AI Agent

Ce projet permet de charger de la documentation MongoDB dans MongoDB Atlas, de générer des embeddings avec Voyage AI, puis de poser des questions à un agent IA qui recherche dans la documentation grâce à la recherche vectorielle.

Il est conçu pour être un projet pédagogique : il montre comment combiner :
- MongoDB Atlas
- Hugging Face datasets
- Voyage AI embeddings
- LangGraph
- LangChain Groq
- un agent avec outils

---

## 1. À quoi sert ce projet ?

Le but est d’avoir un assistant capable de répondre à des questions sur la documentation MongoDB.

Le flux est simple :
1. On charge des documents MongoDB depuis Hugging Face.
2. On les enregistre dans MongoDB.
3. On génère des embeddings pour les chunks de texte.
4. On interroge MongoDB avec une recherche vectorielle.
5. L’agent utilise ces résultats pour répondre à la question de l’utilisateur.

Cela permet de créer une base de connaissances intelligente et exploitable par un chatbot.

---

## 2. Structure du projet

Voici les fichiers principaux :

- `data.py` : charge les données, les insère dans MongoDB et génère les embeddings.
- `main.py` : crée le workflow LangGraph avec l’agent IA et les outils.
- `key_param.py` : lit les clés API depuis les variables d'environnement (ce fichier reste local).
- `key_param.example.py` : modèle de configuration sans secrets.
- `pyproject.toml` : décrit les dépendances Python du projet.

---

## 3. Prérequis

Avant de démarrer, il faut avoir :

- Python 3.10 ou supérieur
- `uv` installé
- un compte MongoDB Atlas
- une clé API Groq
- une clé API Voyage AI
- accès internet pour télécharger les datasets Hugging Face

Vérifie aussi que tu as installé les outils suivants :

- Python
- `uv`
- Git

---

## 4. Installation

Ouvre un terminal à la racine du projet puis exécute :

```bash
uv sync
```

Cela crée l’environnement virtuel et installe les dépendances définies dans `pyproject.toml`.

---

## 5. Configuration des clés

Crée un fichier local `key_param.py` à partir de `key_param.example.py`, puis définis ces variables d'environnement :

```python
MONGODB_URI="..."
GROQ_API_KEY="..."
VOYAGE_API_KEY="..."
```

Remplace ces valeurs par les tiennes.

Important :
- `mongodb_uri` doit être une URL MongoDB Atlas valide.
- `groq_api_key` doit être une clé active Groq.
- `voyage_api_key` doit être une clé active Voyage AI.

Voici un exemple de format de `mongodb_uri` :

```python
mongodb_uri = "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
```

---

## 6. Lancer le script de chargement des données

Le fichier `data.py` permet de remplir MongoDB avec les documents et les embeddings.

Exécute :

```bash
uv run data.py
```

Ce script va :
1. Charger les jeux de données MongoDB depuis Hugging Face.
2. Se connecter à MongoDB Atlas.
3. Vider les collections `full_docs` et `chunked_docs`.
4. Insérer les documents complets.
5. Générer les embeddings avec Voyage AI.
6. Insérer les morceaux de documents avec leurs vecteurs.

Si tout marche bien, tu devrais voir des messages comme :

```text
🚀 Chargement des jeux de données depuis Hugging Face...
🔌 Connexion à MongoDB Atlas...
✅ 20 documents complets insérés.
🎉 Données chargées et indexées avec succès dans MongoDB !
```

---

## 7. Lancer l’agent IA

Le fichier `main.py` lance le workflow LangGraph.

Exécute :

```bash
uv run main.py
```

Le programme va :
1. Charger la connexion MongoDB.
2. Initialiser le modèle Groq.
3. Créer le workflow avec les outils.
4. Demander à l’agent une question.
5. Utiliser la recherche vectorielle pour trouver des réponses dans la documentation.

Exemple :

```text
Quelles sont les bonnes pratiques pour les sauvegardes MongoDB ?
```

L’agent répond ensuite en s’appuyant sur les chunks de documents trouvés dans MongoDB.

---

## 8. Comment fonctionne le projet ?

### Partie 1 : données
`data.py` fait le travail de préparation des données dans MongoDB.

### Partie 2 : embeddings
On utilise Voyage AI pour convertir les textes en vecteurs numériques. Ces vecteurs permettent la recherche sémantique.

### Partie 3 : recherche vectorielle
Dans `main.py`, la fonction `get_information_for_question_answering()` :
- transforme la question en embedding
- cherche les meilleurs documents proches dans MongoDB
- renvoie les résultats au LLM

### Partie 4 : agent IA
Le modèle Groq rédige la réponse à partir des résultats trouvés par les outils.

---

## 9. Les outils de l’agent

Le projet expose deux outils :

- `get_information_for_question_answering(query: str)`
  - recherche des informations pertinentes dans les documents chunkés

- `get_page_content_for_summarization(title: str)`
  - récupère le contenu complet d’une page par son titre

Ces outils permettent à l’agent d’aller chercher des données concrètes avant de répondre.

---

## 10. Dépannage courant

### Problème : mauvaise connexion MongoDB
Vérifie :
- l’URL dans `key_param.py`
- le mot de passe Atlas
- les permissions sur le cluster
- le nom de la base et des collections

### Problème : erreur de quota Voyage AI
Le script a été adapté pour réduire la taille des batches. Si le quota est trop petit, il faut :
- attendre quelques minutes
- réduire encore les lots
- ajouter un paiement/plan dans le dashboard Voyage AI

### Problème : modèle Groq introuvable
Vérifie le nom du modèle dans `main.py` et utilise un modèle disponible dans ton compte Groq.

### Problème : dépendances manquantes
Relance :

```bash
uv sync
```

---

## 11. Bonnes pratiques pour continuer

Pour apprendre et améliorer le projet :

- crée un fichier `.env` pour stocker les clés
- ajout un `.gitignore` pour ne pas publier les clés
- ajoute une gestion des logs
- ajoute une interface web ou CLI
- ajoute un test de base pour vérifier les outils

---

## 12. Résumé rapide

Ce projet montre comment construire un assistant IA sur la documentation MongoDB, avec :
- chargement de données
- embeddings vectoriels
- recherche sémantique
- agent IA avec LangGraph
- mémorisation de session

C’est un très bon exemple pour comprendre la synergie entre :
- base de données
- IA générative
- outils d’indexation vectorielle

---

## 13. Prochaines étapes possibles

Tu peux ensuite étendre le projet en :
- ajoutant plus de sources de documentation
- supportant plusieurs langues
- ajoutant une interface pour interroger l’agent
- ajoutant l’authentification utilisateur
- alimentant la base avec plus de documents

---

## 14. Conclusion

Ce projet est un excellent point de départ pour comprendre la création d’un agent IA connecté à une base de données documentaire.

Si tu suis les étapes ci-dessus, tu vas rapidement comprendre comment :
- préparer les données,
- les stocker,
- ajouter des embeddings,
- faire des recherches vectorielles,
- et faire parler un agent IA sur les résultats.

---

## 15. Commandes utiles

```bash
uv sync
uv run data.py
uv run main.py
```

---

Si tu veux, je peux aussi te préparer une version encore plus simple, plus orientée débutant, avec une explication fichier par fichier et un mini schéma du fonctionnement du projet.
