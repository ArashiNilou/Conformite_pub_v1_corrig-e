import base64
from pathlib import Path
import os
from datetime import datetime
import argparse
from typing import Dict, Any, List, Optional, Union, Tuple
import tempfile
import shutil
import sys
import logging
import re
import cv2
import numpy as np
import subprocess
from PIL import Image, ImageEnhance

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TextExtractor")

# Imports pour Docling
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
    EasyOcrOptions,
    TesseractOcrOptions,
    AcceleratorOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption, ConversionStatus
from docling_core.types.doc import DoclingDocument

class TextExtractor:
    """
    Classe pour extraire le texte des images en utilisant Docling
    avec OCR complet de page et autres options avancées
    """
    
    def __init__(self):
        """
        Initialise l'extracteur de texte
        """
        # Mode d'extraction actif (tesseract, easyocr)
        self.mode = "tesseract"
        # Vérifier les moteurs OCR disponibles
        self.available_ocr_engines = self._check_available_ocr_engines()
        logger.info(f"Moteurs OCR disponibles: {', '.join(self.available_ocr_engines.keys())}")
        
    def _check_available_ocr_engines(self) -> dict:
        """
        Vérifie quels moteurs OCR sont disponibles sur le système
        
        Returns:
            dict: Dictionnaire des moteurs OCR disponibles
        """
        available_engines = {}
        
        # Vérifier si Tesseract est installé
        try:
            result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
            version = result.stdout.split("\n")[0]
            available_engines["tesseract"] = version
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
            
        # Vérifier si EasyOCR est disponible
        try:
            import easyocr
            available_engines["easyocr"] = True
        except ImportError:
            pass
            
        return available_engines
        
    def extract_text_with_tesseract(self, image_path: str, lang: str = "fra+eng") -> str:
        """
        Extrait le texte d'une image en utilisant Tesseract directement via subprocess
        
        Args:
            image_path: Chemin vers l'image
            lang: Langues à utiliser pour Tesseract (ex: "fra+eng")
            
        Returns:
            str: Texte extrait
        """
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return ""
            
        # Prétraiter l'image pour améliorer la reconnaissance
        temp_file = None
        try:
            # Ouvrir et améliorer l'image
            img = Image.open(image_path)
            
            # Vérifier si l'image est en niveaux de gris, sinon la convertir
            if img.mode != 'L':
                img = img.convert('L')
                
            # Améliorer le contraste
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Améliorer la netteté
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            
            # Créer un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            
            # Exécuter Tesseract avec différents modes et garder le meilleur résultat
            configs = [
                # Standard sans options spéciales
                f"--psm 3 --dpi 300 -l {lang}",
                
                # Mode texte dense
                f"--psm 6 --dpi 300 -l {lang}",
                
                # Mode ligne unique (utile pour les petits textes)
                f"--psm 7 --dpi 300 -l {lang}"
            ]
            
            results = []
            for config in configs:
                cmd = f"tesseract {temp_file.name} stdout {config}"
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 and result.stdout:
                        # Nettoyer le texte extrait
                        text = result.stdout.strip()
                        # Supprimer les lignes vides multiples
                        text = re.sub(r'\n{3,}', '\n\n', text)
                        results.append(text)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout lors de l'extraction avec config: {config}")
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction avec config {config}: {str(e)}")
            
            # Garder le résultat le plus long
            if results:
                # Trier par longueur et nombre de mots
                results.sort(key=lambda x: (len(x.split()), len(x)), reverse=True)
                logger.info(f"Texte extrait avec succès via Tesseract ({len(results[0])} caractères)")
                return results[0]
            else:
                logger.warning("Aucun texte extrait via Tesseract")
                return ""
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction avec Tesseract: {str(e)}")
            return ""
            
        finally:
            # Nettoyer le fichier temporaire
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                logger.info(f"Fichier temporaire supprimé: {temp_file.name}")
                
    def extract_text_with_easyocr_direct(self, image_path: str, langs: List[str] = None) -> str:
        """
        Extrait le texte d'une image en utilisant EasyOCR directement
        
        Args:
            image_path: Chemin vers l'image
            langs: Liste des langues à utiliser (ex: ["fr", "en"])
            
        Returns:
            str: Texte extrait
        """
        # Par défaut, utiliser français et anglais
        if not langs:
            langs = ["fr", "en"]
            
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return ""
            
        try:
            import easyocr
            
            # Prétraiter l'image pour améliorer la reconnaissance
            img = Image.open(image_path)
            
            # Convertir en RGB si nécessaire
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Améliorer le contraste
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)
            
            # Sauvegarder dans un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.save(temp_file.name, quality=95)
            logger.info(f"Image prétraitée sauvegardée: {temp_file.name}")
            
            # Créer le Reader
            reader = easyocr.Reader(langs, gpu=True, quantize=True)
            
            # Lire le texte avec deux configurations différentes
            results = []
            
            # Config 1: Standard
            try:
                result1 = reader.readtext(
                    temp_file.name,
                    detail=0,
                    paragraph=True,
                    width_ths=0.7,
                    height_ths=0.7
                )
                if result1:
                    results.append("\n".join(result1))
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction standard avec EasyOCR: {str(e)}")
                
            # Config 2: Optimisée pour le texte dense
            try:
                result2 = reader.readtext(
                    temp_file.name,
                    detail=0,
                    paragraph=False,
                    width_ths=0.5,
                    height_ths=0.5
                )
                if result2:
                    results.append("\n".join(result2))
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction optimisée avec EasyOCR: {str(e)}")
                
            # Nettoyer le fichier temporaire
            os.unlink(temp_file.name)
            
            # Garder le résultat le plus long
            if results:
                # Trier par longueur
                results.sort(key=len, reverse=True)
                logger.info(f"Texte extrait avec succès via EasyOCR ({len(results[0])} caractères)")
                return results[0]
            else:
                logger.warning("Aucun texte extrait via EasyOCR")
                return ""
                
        except ImportError:
            logger.error("EasyOCR n'est pas installé")
            return ""
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction avec EasyOCR: {str(e)}")
            return ""
            
    def extract_text(self, image_path: str, mode: str = None, fallback: bool = True) -> str:
        """
        Extrait le texte d'une image en utilisant la méthode spécifiée
        
        Args:
            image_path: Chemin vers l'image
            mode: Mode d'extraction ('tesseract', 'easyocr')
            fallback: Essayer d'autres méthodes si celle spécifiée échoue
            
        Returns:
            str: Texte extrait
        """
        active_mode = mode or self.mode
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            logger.error(f"Image non trouvée: {image_path}")
            return f"ERREUR: Image non trouvée: {image_path}"
        
        # Essayer d'abord la méthode demandée
        try:
            logger.info(f"Tentative d'extraction avec mode: {active_mode}")
            
            if active_mode == "tesseract" and "tesseract" in self.available_ocr_engines:
                extracted_text = self.extract_text_with_tesseract(image_path)
            elif active_mode == "easyocr" and "easyocr" in self.available_ocr_engines:
                extracted_text = self.extract_text_with_easyocr_direct(image_path)
            else:
                logger.warning(f"Mode {active_mode} non supporté ou moteur non disponible")
                extracted_text = ""
                
            # Si du texte a été extrait, le retourner
            if extracted_text and len(extracted_text.strip()) > 10:
                return extracted_text
                
        except Exception as e:
            logger.error(f"Erreur avec le mode {active_mode}: {str(e)}")
            extracted_text = ""
        
        # Si aucun texte n'a été extrait et que fallback est activé, essayer d'autres méthodes
        if fallback and (not extracted_text or len(extracted_text.strip()) < 10):
            logger.warning(f"Échec de l'extraction avec {active_mode}, essai d'autres méthodes")
            
            # Essayer les méthodes alternatives
            for engine in self.available_ocr_engines.keys():
                if engine != active_mode:
                    try:
                        logger.info(f"Essai avec moteur alternatif: {engine}")
                        
                        if engine == "tesseract":
                            alternative_text = self.extract_text_with_tesseract(image_path)
                        elif engine == "easyocr":
                            alternative_text = self.extract_text_with_easyocr_direct(image_path)
                        else:
                            continue
                            
                        if alternative_text and len(alternative_text.strip()) > 10:
                            logger.info(f"Texte extrait avec succès via {engine}")
                            return alternative_text
                            
                    except Exception as e:
                        logger.warning(f"Erreur avec le moteur alternatif {engine}: {str(e)}")
        
        # Si toujours pas de texte, essayer une dernière approche directe avec tesseract
        if not extracted_text or len(extracted_text.strip()) < 10:
            try:
                # Dernière tentative avec tesseract en ligne de commande directe
                cmd = f"tesseract {image_path} stdout --psm 11 -l fra+eng"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout and len(result.stdout.strip()) > 10:
                    logger.info("Texte extrait avec succès via appel direct à tesseract")
                    return result.stdout.strip()
            except Exception:
                pass
        
        return extracted_text or ""
        
    def batch_extract(self, file_paths: List[str], mode: str = None) -> Dict[str, str]:
        """
        Extrait le texte de plusieurs fichiers
        
        Args:
            file_paths: Liste des chemins des fichiers
            mode: Mode d'extraction
            
        Returns:
            Dict[str, str]: Dictionnaire {chemin: texte}
        """
        results = {}
        
        for file_path in file_paths:
            try:
                text = self.extract_text(file_path, mode)
                results[file_path] = text
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction pour {file_path}: {str(e)}")
                results[file_path] = f"ERREUR: {str(e)}"
                
        return results


if __name__ == "__main__":
    # Permet d'exécuter le script directement pour tester
    parser = argparse.ArgumentParser(description="Extrait le texte d'une image")
    parser.add_argument("image_path", help="Chemin vers l'image pour extraire le texte")
    parser.add_argument("--mode", choices=["tesseract", "easyocr"], 
                        default="tesseract", help="Mode d'extraction de texte")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Afficher les messages de débogage")
    
    args = parser.parse_args()
    
    # Configurer le niveau de log
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    extractor = TextExtractor()
    
    try:
        text = extractor.extract_text(args.image_path, args.mode)
        
        print("\n📝 Texte extrait:")
        print("-" * 50)
        print(text)
        print("-" * 50)
    except Exception as e:
        print(f"❌ Erreur: {str(e)}") 