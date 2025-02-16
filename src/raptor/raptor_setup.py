import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.packs.raptor import RaptorRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from models.ai_models import AIModels
from prompts.prompts import search_query
from time import sleep
from tenacity import retry, stop_after_attempt, wait_exponential

class RaptorSetup:
    """Configuration et initialisation de Raptor"""
    def __init__(self, ai_models: AIModels):
        # Initialisation de la base de données
        self.client = chromadb.PersistentClient(path="./RAPTOR_db")
        self.collection = self.client.get_or_create_collection("legislation_PUB")
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        # Initialisation du retriever avec un cache
        self.retriever = RaptorRetriever(
            [],
            embed_model=ai_models.embedding_model,
            llm=ai_models.llm,
            vector_store=self.vector_store,
            similarity_top_k=3,
            mode="tree_traversal",
        )
        
        # Cache pour les résultats de recherche
        self._search_cache = {}
        
        # Initialisation du query engine
        self.query_engine = RetrieverQueryEngine.from_args(
            self.retriever,
            llm=ai_models.llm
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search(self, query: str) -> str:
        """
        Recherche la législation applicable dans la base de connaissances
        
        Args:
            query: Contexte de la recherche
            
        Returns:
            str: Textes de loi trouvés
        """
        # Vérifier le cache
        if query in self._search_cache:
            print("\n📚 Utilisation du cache pour la recherche...")
            return self._search_cache[query]
        
        print(f"\n📚 Recherche de législation pour: {query[:200]}...")
        
        # Construire la requête de recherche
        formatted_query = search_query.format(query=query)
        print(f"\nRequête formatée: {formatted_query[:200]}...")
        
        try:
            # Récupérer les documents pertinents avec retry
            results = self.retriever.retrieve(formatted_query)
            print(f"\nNombre de résultats trouvés : {len(results)}")
            
            # Extraire le texte des résultats
            text_results = []
            for node in results:
                if hasattr(node, 'text'):
                    text_results.append(node.text)
                elif hasattr(node, 'content'):
                    text_results.append(node.content)
            
            result_text = "\n".join(text_results) if text_results else "Aucune législation trouvée."
            print(f"\nLongueur du texte trouvé : {len(result_text)} caractères")
            
            # Mettre en cache le résultat
            self._search_cache[query] = result_text
            
            # Attendre entre les requêtes
            sleep(2)
            
            return result_text
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la recherche : {str(e)}")
            raise

    def query(self, query_text: str) -> str:
        """
        Exécute une requête via le query engine
        
        Args:
            query_text: La question à poser
            
        Returns:
            str: La réponse générée
        """
        print(f"\n📚 Exécution de la requête Raptor: {query_text[:200]}...")
        try:
            # Utiliser directement les résultats de la recherche précédente si disponible
            if hasattr(self, '_last_search_results'):
                response = self.llm.complete(query_text + "\n\nContexte:\n" + self._last_search_results)
                return str(response)
            
            # Sinon, utiliser le query engine
            response = self.query_engine.query(query_text)
            return str(response)
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la requête Raptor: {str(e)}")
            raise 