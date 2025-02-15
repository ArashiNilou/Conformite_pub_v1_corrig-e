import asyncio
import argparse
from pathlib import Path
from config.azure_config import AzureConfig
from models.ai_models import AIModels
from tools.tools import Tools
from raptor.raptor_setup import RaptorSetup
from agent.react_agent import create_react_agent

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
    agent = initialize_system()
    
    # Construction de la requête
    query = f"Analyse cette image publicitaire et vérifie sa conformité : {image_path}"
    
    print("🔍 Analyse en cours...")
    try:
        response = await agent.achat(query)
        print("\n📋 Résultats de l'analyse :")
        print(str(response))
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse : {str(e)}")

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
    asyncio.run(analyze_image(args.image_path))

if __name__ == "__main__":
    main() 