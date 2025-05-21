import os
from dotenv import load_dotenv
from typing import Optional

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

class AzureConfig:
    """Configuration pour Azure OpenAI chargée depuis les variables d'environnement."""
    API_KEY: Optional[str] = os.getenv("AZURE_API_KEY")
    ENDPOINT: Optional[str] = os.getenv("AZURE_ENDPOINT")
    API_VERSION: Optional[str] = os.getenv("AZURE_API_VERSION")

    def __init__(self):
        """Vérifie que les variables d'environnement nécessaires sont définies."""
        if not self.API_KEY:
            raise ValueError("La variable d'environnement AZURE_API_KEY n'est pas définie.")
        if not self.ENDPOINT:
            raise ValueError("La variable d'environnement AZURE_ENDPOINT n'est pas définie.")
        if not self.API_VERSION:
            raise ValueError("La variable d'environnement AZURE_API_VERSION n'est pas définie.")

