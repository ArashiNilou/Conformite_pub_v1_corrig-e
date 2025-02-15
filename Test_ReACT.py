from llama_index.core.agent import ReActAgent
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock, MessageRole
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core.schema import Document, MediaResource
from llama_index.packs.raptor import RaptorRetriever
import chromadb
import base64
from typing import Optional

from prompts.prompts import description_prompt

class AzureConfig:
    """Configuration pour Azure OpenAI"""
    API_KEY: str = "0ffa834f7af54b5baef1e879dee6a722"
    ENDPOINT: str = "https://additi-dalle-dev.openai.azure.com/"
    API_VERSION: str = "2024-02-15-preview"
    
class AIModels:
    """Initialisation des modèles AI"""
    def __init__(self, config: AzureConfig):
        self.embedding_model = AzureOpenAIEmbedding(
            engine="text-embedding-3-large",
            model="text-embedding-3-large",
            api_key=config.API_KEY,
            azure_endpoint=config.ENDPOINT,
            api_version=config.API_VERSION,
        )
        
        self.llm = AzureOpenAI(
            azure_endpoint=config.ENDPOINT,
            engine="gpt-4o",
            api_version=config.API_VERSION,
            model="gpt-4o",
            api_key=config.API_KEY,
            supports_content_blocks=True
        )

class Tools:
    """Collection des outils disponibles"""
    def __init__(self, llm: AzureOpenAI):
        self.llm = llm
    
    def query_raptor(self, query: str) -> str:
        """Interroge l'API Raptor"""
        return "Raptor is a tool that can be used to query the Raptor API."

    def get_image_description(self, image_path: str) -> str:
        """
        Obtient une description détaillée d'une image en utilisant GPT-4V
        Args:
            image_path: Chemin vers l'image à analyser
        Returns:
            str: Description détaillée de l'image
        """
        # Lire l'image et la convertir en base64
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read())

        # Créer le document image
        image_document = Document(image_resource=MediaResource(data=img_data))

        # Créer le message pour l'analyse de l'image
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=description_prompt),
                ImageBlock(image=image_document.image_resource.data),
            ],
        )

        # Obtenir la description de l'image via GPT-4V
        response = self.llm.chat(messages=[msg])
        return str(response)

    def get_clarifications(self, query: str) -> str:
        """Obtient des clarifications sur la requête"""
        return "Get the clarifications of the query."

    def get_additional_info(self, query: str) -> str:
        """Obtient des informations supplémentaires"""
        return "Get the additional info of the query."

class RaptorSetup:
    """Configuration et initialisation de Raptor"""
    def __init__(self, ai_models: AIModels):
        self.client = chromadb.PersistentClient(path="./RAPTOR_db")
        self.collection = self.client.get_or_create_collection("legislation_PUB")
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        
        self.retriever = RaptorRetriever(
            [],
            embed_model=ai_models.embedding_model,
            llm=ai_models.llm,
            vector_store=self.vector_store,
            similarity_top_k=5,
            mode="tree_traversal",
        )

def initialize_system():
    """Initialise tous les composants du système"""
    config = AzureConfig()
    ai_models = AIModels(config)
    tools = Tools(ai_models.llm)
    raptor = RaptorSetup(ai_models)
    return ai_models, tools, raptor

if __name__ == "__main__":
    ai_models, tools, raptor = initialize_system()