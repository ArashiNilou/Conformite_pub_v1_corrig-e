# LegalVision ReAct Document Analysis Project

## Description

Ce projet implémente un agent IA basé sur l'architecture ReAct (Reasoning and Acting) pour analyser des documents (images ou fichiers PDF). Il utilise des modèles de langage et de vision hébergés sur Azure, une base de connaissances structurée avec RAPTOR (via LlamaIndex), et une série d'outils spécialisés pour effectuer des analyses détaillées comme la vérification de cohérence, l'analyse de conformité, l'extraction d'informations spécifiques (dates, législation), etc.

Le système est conçu pour traiter un document en plusieurs étapes en faisant appel à différents outils de manière autonome pour répondre à une requête ou effectuer une analyse complète.

## Structure du Projet

```
.
├── data/               # Données brutes ou exemples de documents
├── src/                # Code source principal de l'application
│   ├── agent/          # Logique de l'agent ReAct
│   ├── config/         # Fichiers ou classes de configuration (ex: Azure)
│   ├── models/         # Gestion des modèles IA (LLM, Vision)
│   ├── prompts/        # Prompts utilisés par l'agent et les outils
│   ├── raptor/         # Implémentation et gestion de la base RAPTOR
│   ├── tools/          # Outils spécifiques appelés par l'agent
│   ├── utils/          # Fonctions utilitaires (conversion PDF, sauvegarde, etc.)
│   └── main.py         # Point d'entrée principal de l'application
├── RAPTOR_db/          # Base de données générée par RAPTOR
├── outputs/            # Répertoire de sortie pour les résultats d'analyse
├── tests/              # Tests unitaires ou d'intégration (à confirmer)
├── requirements.txt    # Dépendances Python du projet
└── README.md           # Ce fichier
```

## Installation

### Prérequis

*   Python 3.x (vérifier la version exacte si nécessaire)
*   Accès configuré à Azure OpenAI (Clés API, endpoint)
*   Conda pour la gestion de l'environnement

### Étapes d'installation

1.  **Cloner le dépôt** (si ce n'est pas déjà fait) :
    ```bash
    git clone git@gitlab.com:additi/internal/pole-innovation/legalite-pubs.git
    cd legalite-pubs
    ```

2.  **Créer un environnement conda** (recommandé) :
    ```bash
    conda create --name legalvision_env python=3.10.16
    conda activate legalvision_env
    ```

3.  **Installer les dépendances** :
    ```bash
    conda install --file requirements.txt
    pip install llama-index-vector-stores-chroma llama-index-llms-azure-openai llama-index-embeddings-azure-openai llama-index-packs-raptor PyMuPDF opencv-python docling
    ```

4.  **Configuration Azure** :
    Assurez-vous que les variables d'environnement ou un fichier de configuration contiennent les informations nécessaires pour se connecter aux services Azure OpenAI (Endpoint, Clé API).

## Utilisation

Le script principal pour lancer une analyse est `src/main.py`.

**Exemple de commande (à adapter selon les arguments réels) :**

```bash
python src/main.py --file /chemin/vers/votre/document.pdf
# ou pour un dossier
python src/main.py --dir /chemin/vers/votre/dossier
```

Il est probable qu'il existe d'autres arguments pour spécifier le type d'analyse, le mode, etc. Consulter `src/main.py` ou ajouter une aide (`--help`) pour plus de détails.

Les résultats de l'analyse sont généralement sauvegardés dans le répertoire `outputs/`.

## Fonctionnement Interne (Aperçu)

1.  **Initialisation** : Chargement de la configuration, initialisation des modèles IA et des outils.
2.  **Préparation de l'entrée** : Si un PDF est fourni, il est converti en image.
3.  **Agent ReAct** : L'agent reçoit une tâche (implicite ou explicite) concernant le document.
4.  **Cycle Pensée-Action-Observation** :
    *   **Pensée** : L'agent décide quelle action/outil utiliser ensuite.
    *   **Action** : L'agent appelle l'outil choisi (ex: `analyze_vision`, `verify_dates`, `search_legislation`, `extract_raw_text`).
    *   **Observation** : L'agent reçoit le résultat de l'outil.
5.  **Itération** : Le cycle se répète jusqu'à ce que l'agent juge avoir terminé la tâche.
6.  **Résultat Final** : L'agent produit une réponse finale ou un résumé des étapes.
7.  **RAPTOR** : La base de connaissances RAPTOR est utilisée par certains outils (probablement `search_legislation` ou d'autres nécessitant des connaissances externes) pour récupérer des informations pertinentes.

## Tests

(Section à compléter si des informations sur les tests sont disponibles, par exemple comment lancer les tests situés dans `tests/` ou le fichier `Test_ReACT.py`).

## Contribution

(Section à compléter si des directives de contribution existent).
