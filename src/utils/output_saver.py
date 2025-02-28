import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import os
import shutil

class OutputSaver:
    """Gère la sauvegarde des résultats d'analyse en JSON"""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialise le gestionnaire de sauvegarde
        
        Args:
            output_dir: Répertoire de sauvegarde des résultats
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_analysis: Dict[str, Any] = {
            "timestamp": "",
            "image_path": "",
            "vision_result": "",
            "consistency_check": "",
            "legislation": "",
            "clarifications": "",
            "compliance_analysis": ""
        }
    
    def _generate_filename(self, image_path: str) -> str:
        """
        Génère un nom de fichier unique pour les résultats
        
        Args:
            image_path: Chemin de l'image analysée
            
        Returns:
            str: Nom du fichier de sauvegarde
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        return f"analyse_{image_name}_{timestamp}.json"
    
    def start_new_analysis(self, image_path: str) -> None:
        """
        Démarre une nouvelle analyse
        
        Args:
            image_path: Chemin de l'image à analyser
        """
        self.current_analysis = {
            "timestamp": datetime.now().isoformat(),
            "image_path": str(image_path),
            "vision_result": "",
            "consistency_check": "",
            "legislation": "",
            "clarifications": "",
            "compliance_analysis": ""
        }
    
    def save_vision_result(self, result: str) -> None:
        """Sauvegarde le résultat de l'analyse visuelle"""
        self.current_analysis["vision_result"] = result
        self._save_current_analysis()
    
    def save_consistency_check(self, result: str) -> None:
        """Sauvegarde le résultat de la vérification de cohérence"""
        self.current_analysis["consistency_check"] = result
        self._save_current_analysis()
    
    def save_legislation(self, result: str) -> None:
        """Sauvegarde la législation trouvée"""
        self.current_analysis["legislation"] = result
        self._save_current_analysis()
    
    def save_clarifications(self, result: str) -> None:
        """Sauvegarde les clarifications"""
        self.current_analysis["clarifications"] = result
        self._save_current_analysis()
    
    def save_compliance_analysis(self, result: str) -> None:
        """Sauvegarde l'analyse de conformité"""
        self.current_analysis["compliance_analysis"] = result
        self._save_current_analysis()
    
    def _save_current_analysis(self) -> None:
        """Sauvegarde l'analyse en cours dans un fichier JSON"""
        if not self.current_analysis["image_path"]:
            raise ValueError("Aucune analyse en cours")
            
        filename = self._generate_filename(self.current_analysis["image_path"])
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_analysis, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Résultats sauvegardés dans : {output_path}")

def save_output(input_path: str, analysis_data: Dict[str, Any]) -> str:
    """
    Sauvegarde les résultats d'analyse dans un fichier JSON
    
    Args:
        input_path: Chemin du fichier d'entrée
        analysis_data: Données d'analyse à sauvegarder
        
    Returns:
        str: Chemin du fichier JSON créé
    """
    try:
        # Créer le dossier de base s'il n'existe pas
        base_output_dir = Path(__file__).parent.parent.parent / "outputs"
        base_output_dir.mkdir(exist_ok=True)
        
        # Créer un sous-dossier avec la date
        today = datetime.now().strftime("%Y%m%d")
        date_dir = base_output_dir / today
        date_dir.mkdir(exist_ok=True)
        
        # Créer un sous-dossier avec le nom du fichier source
        input_file = Path(input_path)
        source_name = Path(input_file.stem).stem
        source_dir = date_dir / source_name
        source_dir.mkdir(exist_ok=True)
        
        # Générer le nom du fichier de sortie
        timestamp = datetime.now().strftime("%H%M%S")
        output_filename = f"analyse_{timestamp}.json"
        output_path = source_dir / output_filename
        
        # Nettoyer les données d'analyse
        clean_data = {
            "input_file": str(input_file.absolute()),
            "converted_file": analysis_data.get("converted_file"),
            "timestamp": analysis_data.get("timestamp"),
            "steps": {
                "vision_analysis": analysis_data.get("steps", {}).get("vision_analysis", ""),
                "consistency_check": analysis_data.get("steps", {}).get("consistency_check", ""),
                "legislation": analysis_data.get("steps", {}).get("legislation", ""),
                "clarifications": analysis_data.get("steps", {}).get("clarifications", ""),
                "compliance_analysis": analysis_data.get("steps", {}).get("compliance_analysis", "")
            },
            "final_response": analysis_data.get("final_response", "")
        }
        
        # Sauvegarder en JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
            
        # Copier l'image convertie si elle existe
        if clean_data.get("converted_file"):
            image_path = Path(clean_data["converted_file"])
            if image_path.exists():
                image_output = source_dir / f"image_{timestamp}{image_path.suffix}"
                shutil.copy2(image_path, image_output)
                
        return str(output_path.relative_to(base_output_dir.parent))
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {str(e)}")
        print("📝 Détails de l'erreur :")
        import traceback
        print(traceback.format_exc())
        raise 