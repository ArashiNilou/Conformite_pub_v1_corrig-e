import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Ajoute le dossier src au PYTHONPATH

import chromadb
import logging
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document, BaseNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.packs.raptor import RaptorPack
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from typing import List, Any
from config.azure_config import AzureConfig
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniqueIDVectorStore(ChromaVectorStore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id_counter = 0
    
    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Add nodes with unique IDs."""
        embeddings = []
        metadatas = []
        ids = []
        documents = []
        
        for node in nodes:
            embeddings.append(node.get_embedding())
            metadata = node_to_metadata_dict(node, remove_text=True)
            metadatas.append(metadata)
            
            # Générer un ID unique avec un compteur
            unique_id = f"node_{self._id_counter}"
            self._id_counter += 1
            ids.append(unique_id)
            
            documents.append(node.get_content())
        
        self._collection.add(
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
            documents=documents,
        )
        return ids

class RaptorDBInitializer:
    """Initialise la base de données ChromaDB avec les textes de loi"""
    
    def __init__(self, db_path: str = "./RAPTOR_db", data_path: str = "./data/legislation"):
        """
        Initialise l'objet
        
        Args:
            db_path: Chemin vers la base de données ChromaDB
            data_path: Chemin vers le dossier contenant les fichiers PDF de législation
        """
        self.db_path = Path(db_path)
        self.data_path = Path(data_path)
        
        # Configuration Azure
        self.config = AzureConfig()
        
        # Initialisation de ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection("legislation_PUB")
        
        # Initialisation des modèles Azure
        self.embedding_model = AzureOpenAIEmbedding(
            engine="text-embedding-3-large",
            model="text-embedding-3-large",
            api_key=self.config.API_KEY,
            azure_endpoint=self.config.ENDPOINT,
            api_version=self.config.API_VERSION,
        )
        
        self.llm = AzureOpenAI(
            azure_endpoint=self.config.ENDPOINT,
            engine="gpt4o",
            api_version=self.config.API_VERSION,
            model="gpt-4o",
            api_key=self.config.API_KEY,
            temperature=0.1
        )
        
    def initialize_raptor_pack(self, documents: List[Document]) -> RaptorPack:
        """
        Initialise RaptorPack avec les documents et les modèles configurés
        """
        # Créer le vector store
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        # Créer RaptorPack avec des paramètres optimisés
        raptor_pack = RaptorPack(
            documents=documents,
            embed_model=self.embedding_model,
            llm=self.llm,
            vector_store=vector_store,
            similarity_top_k=1,  # Réduit à 1 pour avoir le document le plus pertinent
            mode="tree-traversal",  # Mode plus simple
            transformations=[
                SentenceSplitter(
                    chunk_size=256,  # Réduit la taille des chunks
                    chunk_overlap=20  # Réduit le chevauchement
                )
            ]
        )
        
        return raptor_pack
    
    def load_legislation_data(self) -> List[Document]:
        """
        Charge les données de législation depuis les fichiers PDF
        
        Returns:
            List[Document]: Liste des documents chargés
        """
        # Créer le dossier data s'il n'existe pas
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔍 Recherche de documents dans {self.data_path}")
        
        # Utiliser SimpleDirectoryReader pour charger les documents
        reader = SimpleDirectoryReader(
            input_dir=str(self.data_path),
            recursive=True,  # Lire les sous-dossiers
            required_exts=[".pdf"]  # Ne lire que les PDFs
        )
        
        # Charger les documents
        try:
            documents = reader.load_data()
            logger.info(f"✅ {len(documents)} documents chargés")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des documents: {e}")
            raise
    
    def initialize_db(self):
        """Initialise la base de données avec les textes de loi"""
        try:
            # Supprimer et recréer la collection
            collections = self.client.list_collections()
            if "legislation_PUB" in collections:
                logger.info("Suppression de l'ancienne collection...")
                self.client.delete_collection("legislation_PUB")
            
            # Recréer la collection
            self.collection = self.client.create_collection(
                name="legislation_PUB",
                metadata={"description": "Base de législation publicitaire"}
            )
            logger.info("✅ Collection recréée avec succès")
            
            # Charger les documents
            documents = self.load_legislation_data()
            
            if not documents:
                logger.warning("⚠️ Aucun document trouvé. Vérifiez vos fichiers PDF.")
                return
                
            # Assigner des IDs uniques aux documents
            for i, doc in enumerate(documents):
                doc.id_ = f"doc_{i}"
                if hasattr(doc, 'node_id'):
                    doc.node_id = f"node_{i}"
            
            logger.info(f"📄 Indexation de {len(documents)} documents...")
            
            # Initialiser et utiliser RaptorPack
            raptor_pack = self.initialize_raptor_pack(documents)
            
            logger.info(f"✅ Base de données initialisée avec {self.collection.count()} nodes")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
            raise

def main():
    """Point d'entrée pour l'initialisation de la base de données"""
    try:
        initializer = RaptorDBInitializer()
        initializer.initialize_db()
        logger.info("✅ Initialisation terminée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        raise

if __name__ == "__main__":
    main() 