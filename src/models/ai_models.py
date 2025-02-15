from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from config.azure_config import AzureConfig

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
            engine="gpt4o",
            api_version=config.API_VERSION,
            model="gpt-4o",
            api_key=config.API_KEY,
            supports_content_blocks=True
        ) 