import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.azure_config import AzureConfig
from models.ai_models import AIModels
from tools.tools import Tools
from raptor.raptor_setup import RaptorSetup
from agent.react_agent import create_react_agent
from llama_index.core.callbacks import CBEventType, CallbackManager
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from PIL import Image
import io
import os
import sys
from utils.pdf_converter import convert_pdf_to_image
from utils.output_saver import save_output
import json
from datetime import datetime

class CustomCallbackHandler(BaseCallbackHandler):
    """Handler personnalisé pour logger les événements de l'agent"""
    
    def __init__(self) -> None:
        super().__init__([], [])
        print("\n🔄 Initialisation du CustomCallbackHandler")
        self.steps = {
            "vision_analysis": "",
            "consistency_check": "",
            "legislation": "",
            "clarifications": "",
            "compliance_analysis": ""
        }
        print("✅ Steps initialisés :", self.steps.keys())
        self.current_action = None
        
    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Log le début d'un événement"""
        if event_type == CBEventType.FUNCTION_CALL and payload:
            tool_metadata = payload.get("tool", {})
            if hasattr(tool_metadata, "name"):
                self.current_action = tool_metadata.name
                print(f"✅ Action courante mise à jour: {self.current_action}")
        
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Log la fin d'un événement"""
        if event_type == CBEventType.FUNCTION_CALL and payload:
            if "function_call_response" in payload:
                print(f"\n{'='*50}")
                print(f"📝 Traitement de la réponse pour l'action: {self.current_action}")
                response = str(payload["function_call_response"])
                
                # Stocker la réponse selon l'action
                if self.current_action == "analyze_vision":
                    print("💾 Sauvegarde de l'analyse visuelle...")
                    self.steps["vision_analysis"] = response
                elif self.current_action == "verify_consistency":
                    print("💾 Sauvegarde de la vérification de cohérence...")
                    self.steps["consistency_check"] = response
                elif self.current_action == "search_legislation":
                    print("💾 Sauvegarde de la législation...")
                    self.steps["legislation"] = response
                elif self.current_action == "get_clarifications":
                    print("💾 Sauvegarde des clarifications...")
                    self.steps["clarifications"] = response
                elif self.current_action == "analyze_compliance":
                    print("💾 Sauvegarde de l'analyse de conformité...")
                    self.steps["compliance_analysis"] = response
                
                print(f"{'='*50}\n")

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

def initialize_system(callback_handler):
    """Initialise tous les composants du système"""
    config = AzureConfig()
    ai_models = AIModels(config)
    raptor = RaptorSetup(ai_models)
    tools = Tools(ai_models.llm, raptor)
    
    # Créer un CallbackManager avec notre handler
    callback_manager = CallbackManager([callback_handler])
    
    agent = create_react_agent(
        ai_models=ai_models, 
        tools=tools, 
        callback_manager=callback_manager,
        verbose=True
    )
    return agent

async def analyze_image(image_path: str) -> None:
    """
    Analyse une image publicitaire
    
    Args:
        image_path: Chemin vers l'image à analyser
    """
    try:
        original_path = image_path
        if image_path.lower().endswith('.pdf'):
            print("📄 Conversion du PDF en image...")
            image_path = convert_pdf_to_image(image_path)
        
        print("🔧 Initialisation du système...")
        callback_handler = CustomCallbackHandler()
        agent = initialize_system(callback_handler)
        
        query = f"Analyse cette image publicitaire et vérifie sa conformité : {image_path}"
        
        print("🔍 Analyse en cours...")
        try:
            print("⏳ Envoi de la requête à l'agent...")
            response = await agent.achat(query)
            
            print("\n🔍 Préparation des données pour le JSON...")
            # Préparer les données avec toutes les étapes
            analysis_data = {
                "input_file": original_path,
                "converted_file": image_path if image_path != original_path else None,
                "timestamp": datetime.now().isoformat(),
                "steps": callback_handler.steps,
                "final_response": str(response)
            }
            
            print("\n📊 Contenu du JSON :")
            print(json.dumps(analysis_data, indent=2, ensure_ascii=False))
            
            print("\n💾 Sauvegarde du JSON...")
            # Sauvegarder le fichier JSON unique
            output_path = save_output(original_path, analysis_data)
            print(f"✅ Résultats sauvegardés dans : {output_path}")
            
            print("\n📋 Résultats de l'analyse :")
            print(str(response))
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'analyse : {str(e)}")
            print("📝 Détails de l'erreur :")
            import traceback
            print(traceback.format_exc())
            
    finally:
        if image_path.lower().endswith('.jpg') and image_path != original_path:
            try:
                os.remove(image_path)
                print("🧹 Nettoyage des fichiers temporaires")
            except:
                pass

def validate_image_path(path: str) -> str:
    """
    Valide le chemin de l'image ou du PDF
    
    Args:
        path: Chemin à valider
        
    Returns:
        str: Chemin validé
        
    Raises:
        ArgumentTypeError: Si le chemin n'est pas valide
    """
    file_path = Path(path)
    if not file_path.exists():
        raise argparse.ArgumentTypeError(f"Le fichier {path} n'existe pas")
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"{path} n'est pas un fichier")
    if file_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise argparse.ArgumentTypeError(f"{path} n'est pas un format supporté (formats acceptés : jpg, jpeg, png, pdf)")
    return str(file_path.absolute())

def get_files_to_analyze(path: str) -> List[str]:
    """
    Récupère tous les fichiers à analyser dans un chemin donné
    
    Args:
        path: Chemin vers un fichier ou un dossier
        
    Returns:
        List[str]: Liste des chemins de fichiers à analyser
    """
    path_obj = Path(path)
    supported_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
    processed_files = set()
    excluded_dirs = {'temp_images', 'converted_images'}
    
    # Vérifier les fichiers déjà traités
    if Path("outputs").exists():
        for date_dir in Path("outputs").iterdir():
            if date_dir.is_dir():
                processed_files.update(Path(f.stem).stem for f in date_dir.glob("*/*"))
    
    if path_obj.is_file():
        if path_obj.suffix.lower() in supported_extensions:
            base_name = Path(path_obj.stem).stem
            if base_name not in processed_files:
                return [str(path_obj.absolute())]
            print(f"⏭️  Fichier déjà traité : {path_obj.name}")
            return []
        raise argparse.ArgumentTypeError(f"{path} n'est pas un format supporté (formats acceptés : jpg, jpeg, png, pdf)")
        
    elif path_obj.is_dir():
        files = []
        seen_base_names = set()
        
        # Récupérer tous les fichiers du dossier (non récursif)
        all_files = []
        for ext in supported_extensions:
            # Filtrer les fichiers qui ne sont pas dans les dossiers exclus
            for f in path_obj.glob(f"*{ext}"):
                if not any(excluded in str(f) for excluded in excluded_dirs):
                    all_files.append(f)
            for f in path_obj.glob(f"*{ext.upper()}"):
                if not any(excluded in str(f) for excluded in excluded_dirs):
                    all_files.append(f)
        
        # Trier pour traiter d'abord les PDFs
        all_files = sorted(all_files, key=lambda x: (Path(x.stem).stem, x.suffix != '.pdf'))
        
        # Filtrer les fichiers non traités et éviter les doublons
        for f in all_files:
            base_name = Path(f.stem).stem
            if base_name not in processed_files and base_name not in seen_base_names:
                files.append(f)
                seen_base_names.add(base_name)
            else:
                print(f"⏭️  Fichier déjà traité ou doublon : {f.name}")
                    
        return [str(f.absolute()) for f in files]
        
    raise argparse.ArgumentTypeError(f"Le chemin {path} n'existe pas")

async def analyze_files(files: List[str]) -> None:
    """
    Analyse une liste de fichiers
    
    Args:
        files: Liste des chemins de fichiers à analyser
    """
    total = len(files)
    for i, file_path in enumerate(files, 1):
        print(f"\n📄 Traitement du fichier {i}/{total} : {Path(file_path).name}")
        try:
            await analyze_image(file_path)
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {file_path}: {e}")
            continue

def main():
    """Point d'entrée principal de l'application"""
    try:
        parser = argparse.ArgumentParser(
            description="Analyse de conformité d'images publicitaires",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples d'utilisation:
    python main.py path/to/image.jpg     # Analyser une image
    python main.py path/to/folder/       # Analyser tous les fichiers d'un dossier
    python main.py -r path/to/folder/    # Analyser récursivement tous les fichiers
            """
        )
        
        parser.add_argument(
            'path',
            type=str,
            help='Chemin vers l\'image ou le dossier à analyser'
        )
        
        parser.add_argument(
            '-r', '--recursive',
            action='store_true',
            help='Explorer récursivement les sous-dossiers'
        )

        args = parser.parse_args()
        
        # Récupérer tous les fichiers à analyser
        files = get_files_to_analyze(args.path)
        
        if not files:
            print("⚠️ Aucun fichier à analyser trouvé")
            return
            
        print(f"🔍 {len(files)} fichiers à analyser")
        asyncio.run(analyze_files(files))
        
    except KeyboardInterrupt:
        print("\n⚠️ Programme interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {str(e)}")
        print("📝 Détails de l'erreur :")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 