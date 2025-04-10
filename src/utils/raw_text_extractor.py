#!/usr/bin/env python3
"""
Module d'extraction de texte brut à partir d'images
Ce module est spécialement conçu pour extraire le texte brut sans aucune correction orthographique
"""

import os
import sys
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RawTextExtractor")

class RawTextExtractor:
    """
    Classe pour extraire le texte brut des images sans aucune correction
    orthographique. Préserve le texte tel qu'il est reconnu par l'OCR.
    """
    
    def __init__(self):
        """
        Initialise l'extracteur de texte brut
        """
        # Vérifier les moteurs OCR disponibles
        self.available_engines = self._check_available_engines()
        logger.info(f"Moteurs OCR disponibles: {', '.join(self.available_engines.keys())}")
    
    def _check_available_engines(self) -> Dict[str, bool]:
        """
        Vérifie quels moteurs d'OCR sont disponibles sur le système
        
        Returns:
            Dict[str, bool]: Dictionnaire des moteurs disponibles
        """
        engines = {}
        
        # Vérifier si Tesseract est installé
        try:
            result = subprocess.run(
                ["tesseract", "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            if result.returncode == 0:
                engines["tesseract"] = True
        except FileNotFoundError:
            pass
        
        # Vérifier si EasyOCR est disponible
        try:
            import easyocr
            engines["easyocr"] = True
        except ImportError:
            pass
            
        return engines
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Prétraite l'image pour améliorer la reconnaissance OCR
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            str: Chemin vers l'image prétraitée
        """
        try:
            # Ouvrir l'image
            img = Image.open(image_path)
            
            # Convertir en niveaux de gris si nécessaire
            if img.mode != 'L':
                img = img.convert('L')
            
            # Améliorer le contraste
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Améliorer la netteté
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            
            # Sauvegarder dans un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.save(temp_file.name)
            
            logger.info(f"Image prétraitée sauvegardée: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Erreur lors du prétraitement de l'image: {str(e)}")
            return image_path
    
    def extract_with_tesseract(self, image_path: str, lang: str = "fra+eng") -> str:
        """
        Extrait le texte brut en utilisant Tesseract
        
        Args:
            image_path: Chemin vers l'image
            lang: Langues à utiliser (ex: "fra+eng")
            
        Returns:
            str: Texte extrait
        """
        if "tesseract" not in self.available_engines:
            logger.warning("Tesseract n'est pas installé")
            return ""
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return ""
        
        # Prétraiter l'image
        processed_image = self._preprocess_image(image_path)
        
        try:
            # Extraire le texte avec Tesseract
            result = subprocess.run(
                ["tesseract", processed_image, "stdout", "-l", lang, "--psm", "6"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Nettoyer le fichier temporaire
            if processed_image != image_path:
                os.unlink(processed_image)
            
            if result.returncode != 0:
                logger.error(f"Erreur Tesseract: {result.stderr}")
                return ""
            
            return result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction avec Tesseract: {str(e)}")
            # Nettoyer le fichier temporaire
            if processed_image != image_path:
                try:
                    os.unlink(processed_image)
                except:
                    pass
            return ""
    
    def extract_with_easyocr(self, image_path: str, langs: List[str] = None) -> str:
        """
        Extrait le texte brut en utilisant EasyOCR
        
        Args:
            image_path: Chemin vers l'image
            langs: Langues à utiliser (ex: ["fr", "en"])
            
        Returns:
            str: Texte extrait
        """
        if "easyocr" not in self.available_engines:
            logger.warning("EasyOCR n'est pas installé")
            return ""
        
        if langs is None:
            langs = ["fr", "en"]
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return ""
            
        try:
            import easyocr
            reader = easyocr.Reader(langs)
            
            # Prétraiter l'image
            processed_image = self._preprocess_image(image_path)
            
            # Extraire le texte
            results = reader.readtext(processed_image)
            
            # Nettoyer le fichier temporaire
            if processed_image != image_path:
                os.unlink(processed_image)
            
            # Formater les résultats
            extracted_text = "\n".join([text for _, text, _ in results])
            
            if not extracted_text:
                logger.warning("Aucun texte extrait via EasyOCR")
                
            return extracted_text
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction avec EasyOCR: {str(e)}")
            # Nettoyer le fichier temporaire
            if processed_image != image_path:
                try:
                    os.unlink(processed_image)
                except:
                    pass
            return ""
    
    def extract_raw_text(self, image_path: str, method: str = "auto") -> Dict[str, str]:
        """
        Extrait le texte brut en utilisant la méthode spécifiée ou toutes les méthodes disponibles
        
        Args:
            image_path: Chemin vers l'image
            method: Méthode d'extraction ("tesseract", "easyocr", "auto")
            
        Returns:
            Dict[str, str]: Dictionnaire des résultats par méthode
        """
        results = {}
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return results
        
        # Sélectionner les méthodes à utiliser
        methods_to_use = []
        if method == "auto":
            # Utiliser toutes les méthodes disponibles
            if "tesseract" in self.available_engines:
                methods_to_use.append("tesseract")
            if "easyocr" in self.available_engines:
                methods_to_use.append("easyocr")
        else:
            # Utiliser uniquement la méthode spécifiée
            if method in self.available_engines and self.available_engines[method]:
                methods_to_use.append(method)
        
        # Si aucune méthode n'est disponible, retourner un dictionnaire vide
        if not methods_to_use:
            logger.warning(f"Aucune méthode d'extraction disponible")
            return results
            
        # Extraire le texte avec chaque méthode
        for method in methods_to_use:
            try:
                if method == "tesseract":
                    text = self.extract_with_tesseract(image_path)
                elif method == "easyocr":
                    text = self.extract_with_easyocr(image_path)
                else:
                    logger.warning(f"Méthode d'extraction inconnue: {method}")
                    continue
                
                results[method] = text
                
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction avec {method}: {str(e)}")
                results[method] = f"ERREUR: {str(e)}"
        
        return results

# Fonction principale pour l'exécution en ligne de commande
def main():
    """
    Point d'entrée pour l'exécution en ligne de commande
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Extraction de texte brut à partir d'images")
    parser.add_argument("image", help="Chemin vers l'image à analyser")
    parser.add_argument("--method", choices=["tesseract", "easyocr", "auto"], default="auto",
                     help="Méthode d'extraction de texte (défaut: auto)")
    
    args = parser.parse_args()
    
    # Créer l'extracteur et extraire le texte
    extractor = RawTextExtractor()
    results = extractor.extract_raw_text(args.image, args.method)
    
    # Afficher les résultats
    if not results:
        print("❌ Aucun texte extrait")
        return
    
    for method, text in results.items():
        print(f"\n===== TEXTE EXTRAIT AVEC {method.upper()} =====")
        print(text if text else "[Aucun texte extrait]")
        print("=" * 50)

if __name__ == "__main__":
    main() 