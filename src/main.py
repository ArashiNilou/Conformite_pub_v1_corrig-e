import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from config.azure_config import AzureConfig
from models.ai_models import AIModels
from tools.tools import Tools
from raptor.raptor_setup import RaptorSetup
from agent.react_agent import create_react_agent
from llama_index.core.callbacks import CBEventType
from llama_index.core.callbacks.base_handler import BaseCallbackHandler

class CustomCallbackHandler(BaseCallbackHandler):
    """Handler personnalisé pour logger les événements de l'agent"""
    
    def __init__(self) -> None:
        super().__init__([], [])  # Ne pas ignorer d'événements
        
    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Log le début d'un événement"""
        if event_type == CBEventType.AGENT_STEP:
            print(f"\n🤖 Étape de l'agent - Début")
            if payload and "thought" in payload:
                print(f"💭 Réflexion: {payload['thought']}")
            if payload and "action" in payload:
                print(f"🎯 Action: {payload['action']}")
            if payload and "action_input" in payload:
                print(f"📥 Entrée: {payload['action_input']}")
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Log la fin d'un événement"""
        if event_type == CBEventType.AGENT_STEP:
            if payload and "observation" in payload:
                print(f"👁️ Observation: {payload['observation']}")
            print("🤖 Étape de l'agent - Fin\n")

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        """Début d'une trace"""
        print(f"\n📝 Début de la trace: {trace_id}")

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Fin d'une trace"""
        print(f"📝 Fin de la trace: {trace_id}\n")

def initialize_system():
    """Initialise tous les composants du système"""
    config = AzureConfig()
    ai_models = AIModels(config)
    raptor = RaptorSetup(ai_models)
    tools = Tools(ai_models.llm, raptor)
    agent = create_react_agent(ai_models, tools, verbose=True)
    return agent

async def analyze_image(image_path: str) -> None:
    """
    Analyse une image publicitaire
    
    Args:
        image_path: Chemin vers l'image à analyser
    """
    print("🔧 Initialisation du système...")
    agent = initialize_system()
    
    # Construction de la requête
    query = f"Analyse cette image publicitaire et vérifie sa conformité : {image_path}"
    
    print("🔍 Analyse en cours...")
    try:
        print("⏳ Envoi de la requête à l'agent...")
        response = await agent.achat(query)
        print("\n📋 Résultats de l'analyse :")
        print(str(response))
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse : {str(e)}")
        print("📝 Détails de l'erreur :")
        import traceback
        print(traceback.format_exc())

def validate_image_path(path: str) -> str:
    """
    Valide le chemin de l'image
    
    Args:
        path: Chemin à valider
        
    Returns:
        str: Chemin validé
        
    Raises:
        ArgumentTypeError: Si le chemin n'est pas valide
    """
    image_path = Path(path)
    if not image_path.exists():
        raise argparse.ArgumentTypeError(f"Le fichier {path} n'existe pas")
    if not image_path.is_file():
        raise argparse.ArgumentTypeError(f"{path} n'est pas un fichier")
    if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
        raise argparse.ArgumentTypeError(f"{path} n'est pas une image (formats acceptés : jpg, jpeg, png)")
    return str(image_path.absolute())

def main():
    """Point d'entrée principal de l'application"""
    try:
        parser = argparse.ArgumentParser(
            description="Analyse de conformité d'images publicitaires",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemple d'utilisation:
    python main.py path/to/image.jpg
            """
        )
        
        parser.add_argument(
            'image_path',
            type=validate_image_path,
            help='Chemin vers l\'image à analyser'
        )

        args = parser.parse_args()
        
        print(f"🖼️  Image à analyser : {args.image_path}")
        print("🚀 Démarrage de l'analyse...")
        asyncio.run(analyze_image(args.image_path))
        
    except KeyboardInterrupt:
        print("\n⚠️ Programme interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {str(e)}")
        print("📝 Détails de l'erreur :")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 