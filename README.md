# MongoDB AI Agent

Ce projet permet de charger de la documentation MongoDB dans MongoDB Atlas, de générer des embeddings avec Voyage AI, puis de poser des questions à un agent IA qui recherche dans la documentation grâce à la recherche vectorielle.

Il est conçu pour être un projet pédagogique et combine :
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
- `main.py` : construit le workflow LangGraph, ses outils et son checkpoint MongoDB.
- `streamlit_app.py` : fournit l’interface de chat et le formulaire de configuration des clés.
- `key_param.py` : lit les variables d’environnement utilisées par le script de chargement des données (fichier local).
- `key_param.example.py` : modèle de configuration sans secrets.
- `pyproject.toml` et `uv.lock` : décrivent et verrouillent les dépendances Python, dont Streamlit.

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

L’interface Streamlit demande les trois identifiants dans des champs masqués; ils ne sont pas enregistrés sur disque. Pour charger les données ou lancer le script CLI, configure les variables d’environnement suivantes. `data.py` les lit via `key_param.py` :

```powershell
$env:MONGODB_URI = "mongodb+srv://..."
$env:GROQ_API_KEY = "..."
$env:VOYAGE_API_KEY = "..."
```

Ces commandes PowerShell ne configurent les valeurs que pour le terminal courant. `MONGODB_URI` doit autoriser l’accès au cluster Atlas; les clés Groq et Voyage AI doivent être actives. Ne publie jamais ces valeurs.

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
3. Vider les collections `full_docs` et `chunked_docs` avant de les recharger.
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

Le fichier `main.py` lance le workflow LangGraph en mode terminal et utilise les variables d’environnement.

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

### Tester avec l’interface Streamlit

```bash
uv run streamlit run streamlit_app.py
```

Dans le panneau **Connexion**, saisis l’URI MongoDB et les clés Groq et Voyage AI, puis sélectionne **Vérifier les clés**. L’interface teste le ping MongoDB, l’accès à l’API Groq et un embedding Voyage AI. Le chat n’est activé que si les trois tests réussissent.

Les valeurs sont masquées et conservées en mémoire pour la session Streamlit; elles ne sont écrites ni dans `key_param.py` ni sur disque. Après connexion, pose tes questions dans le champ de chat. Le bouton **Nouvelle conversation** crée un nouvel identifiant de fil; les conversations précédentes ne sont pas supprimées de MongoDB.

Pour que les réponses documentaires fonctionnent, charge d’abord les données avec `data.py` et configure dans MongoDB Atlas l’index de recherche vectorielle `vector_index` sur `ai_agents.chunked_docs`, avec le champ `embedding`.

---

## 8. Comment fonctionne le projet ?

### Partie 1 : données
`data.py` fait le travail de préparation des données dans MongoDB.

### Partie 2 : embeddings
On utilise Voyage AI pour convertir les textes en vecteurs numériques. Ces vecteurs permettent la recherche sémantique.

### Partie 3 : recherche vectorielle
Dans `main.py`, l’outil `get_information_for_question_answering` :
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
- l’URI saisie dans l’interface ou la variable `MONGODB_URI` pour le CLI
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

### Problème : un contrôle de clé échoue dans Streamlit

Le panneau Connexion affiche le résultat séparément pour MongoDB, Groq et Voyage AI. Vérifie le service correspondant, puis saisis de nouveau les trois valeurs et relance **Vérifier les clés**. Les champs ne sont pas préremplis depuis les variables d’environnement.

---

## 11. Sécurité et fonctionnement des sessions

- Ne partage pas les URI ni les clés API et ne les ajoute pas au dépôt.
- L’interface masque les champs de saisie et garde les identifiants dans la mémoire de la session Streamlit.
- La mémoire de conversation LangGraph est stockée dans MongoDB grâce au checkpoint; **Nouvelle conversation** crée un autre fil sans effacer les précédents.
- Les appels de recherche utilisent Voyage AI pour l’embedding et MongoDB Atlas Vector Search pour retrouver les documents.

---

## 12. Résumé rapide

Ce projet montre comment construire un assistant IA sur la documentation MongoDB, avec :
- chargement de données
- embeddings vectoriels
- recherche sémantique
- agent IA avec LangGraph
- mémoire de conversation persistée dans MongoDB
- interface Streamlit avec vérification des clés

C’est un très bon exemple pour comprendre la synergie entre :
- base de données
- IA générative
- outils d’indexation vectorielle

---

## 13. Prochaines étapes possibles

Tu peux ensuite étendre le projet en :
- ajoutant plus de sources de documentation
- supportant plusieurs langues
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
uv run streamlit run streamlit_app.py
```

---

Si tu veux, je peux aussi te préparer une version encore plus simple, plus orientée débutant, avec une explication fichier par fichier et un mini schéma du fonctionnement du projet.
