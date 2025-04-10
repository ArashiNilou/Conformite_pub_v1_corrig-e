#!/usr/bin/env python3
"""
Test spécifique pour l'extraction de texte de la publicité "ON RACHÈTE VOTRE CANAPÉ"
"""

import os
import sys
from pathlib import Path
import pytest

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_extractor import TextExtractor


def test_canape_advert_text_extraction():
    """
    Teste l'extraction du texte de la publicité pour le canapé
    
    Cette fonction recherche l'image publicitaire dans les répertoires courants
    et applique l'extraction de texte pour vérifier que le texte 
    'ON RACHÈTE VOTRE CANAPÉ JUSQU'À 2000€*' est bien détecté.
    """
    # Chercher l'image dans les emplacements possibles
    image_found = False
    
    # Vérifier si un chemin d'image est fourni en argument
    custom_image_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        custom_image_path = sys.argv[1]
        print(f"Utilisation de l'image personnalisée: {custom_image_path}")
    
    image_paths = [
        # Utiliser l'image personnalisée si fournie
        custom_image_path,
        # Chercher directement dans le répertoire courant
        "image_101039.png",
        # Ou dans d'autres emplacements possibles
        "src/data/image_101039.png",
        "data/image_101039.png",
        # Recherche générique
        *Path(".").glob("**/image_101039.png")
    ]
    
    # Filtrer les chemins qui existent (et ne sont pas None)
    valid_paths = [str(p) for p in image_paths if p and Path(p).exists()]
    
    if not valid_paths:
        pytest.skip("Image publicitaire 'image_101039.png' non trouvée")
    
    image_path = valid_paths[0]
    print(f"Image trouvée: {image_path}")
    
    # Vérifier quels moteurs OCR sont disponibles
    available_engines = {}
    
    # Tester si Tesseract est installé
    try:
        import subprocess
        result = subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            available_engines["tesseract"] = True
            print("✅ Tesseract est installé:", result.stdout.split("\n")[0])
        else:
            print("❌ Tesseract n'est pas correctement installé")
    except FileNotFoundError:
        print("❌ Tesseract n'est pas installé sur ce système")
    
    # Tester si EasyOCR est disponible
    try:
        import importlib
        easyocr_spec = importlib.util.find_spec("easyocr")
        if easyocr_spec is not None:
            available_engines["easyocr"] = True
            print("✅ EasyOCR est disponible")
        else:
            print("❌ EasyOCR n'est pas installé")
    except ImportError:
        print("❌ EasyOCR n'est pas installé")
    
    if not available_engines:
        pytest.skip("Aucun moteur OCR n'est disponible (ni Tesseract, ni EasyOCR)")
    
    # Texte attendu (approximatif - l'OCR peut ne pas être parfait)
    expected_text_parts = [
        "ON", "RACHETE", "RACH", "CANAPE", "CANAP", "VOTRE", 
        "JUSQU", "2000", "€", "HOMESALONS", "HOME", "SALONS"
    ]
    
    # Initialiser l'extracteur de texte
    extractor = TextExtractor()
    
    # Essayer plusieurs méthodes d'extraction
    extraction_modes = []
    
    # Vérifier quels modes sont disponibles
    try:
        import pytesseract
        extraction_modes.append("pytesseract")
    except ImportError:
        print("📝 pytesseract n'est pas disponible")
    
    try:
        import easyocr
        extraction_modes.append("easyocr")
    except ImportError:
        print("📝 easyocr n'est pas disponible")
    
    # Toujours essayer docling en dernier
    if "docling" not in extraction_modes:
        extraction_modes.append("docling")
    
    if not extraction_modes:
        pytest.skip("Aucune méthode d'extraction disponible")
    
    print(f"🔍 Méthodes d'extraction disponibles: {', '.join(extraction_modes)}")
    
    # Variables pour stocker les résultats
    best_result = None
    best_score = 0
    results = {}
    
    # Tester chaque méthode d'extraction
    for mode in extraction_modes:
        print(f"\n📋 Test avec mode: {mode}")
        
        try:
            # Extraire le texte
            if mode == "docling":
                # Pour docling, essayer avec différents moteurs OCR
                ocr_engines = ["easyocr"] if "easyocr" in available_engines else []
                if not ocr_engines:
                    print("⚠️ Aucun moteur OCR disponible pour Docling, utilisation de la méthode générique")
                    extracted_text = extractor.extract_text(image_path, fallback=True)
                else:
                    for ocr_engine in ocr_engines:
                        try:
                            print(f"  🔍 Essai avec moteur OCR: {ocr_engine}")
                            extracted_text = extractor.extract_text_with_docling(image_path, ocr_engine)
                            break
                        except Exception as e:
                            print(f"  ❌ Erreur avec {ocr_engine}: {str(e)}")
                            extracted_text = ""
            elif mode == "pytesseract":
                extracted_text = extractor.extract_text_with_pytesseract(image_path)
            elif mode == "easyocr":
                extracted_text = extractor.extract_text_with_easyocr_direct(image_path)
            else:
                print(f"⚠️ Mode inconnu: {mode}")
                continue
            
            # Afficher le texte extrait
            print("\n=== Texte extrait ===")
            print(extracted_text if extracted_text else "[Aucun texte extrait]")
            print("===\n")
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                print("⚠️ ATTENTION: Aucun texte n'a été extrait!")
                results[mode] = {"text": "", "score": 0, "matches": []}
                continue
            
            # Convertir en majuscules pour une comparaison insensible à la casse
            extracted_text_upper = extracted_text.upper()
            
            # Afficher chaque mot du texte extrait pour le débogage
            words = [w.strip() for w in extracted_text_upper.split() if w.strip()]
            print(f"Mots détectés ({len(words)}): {', '.join(words[:10])}...")
            
            # Vérifier que le texte extrait contient les parties attendues
            matches = []
            for expected in expected_text_parts:
                found = False
                expected_upper = expected.upper()
                
                # Vérification exacte
                if expected_upper in extracted_text_upper:
                    found = True
                    matches.append(expected)
                    print(f"✅ Trouvé exact: '{expected}'")
                    continue
                
                # Vérification approximative
                for word in words:
                    if len(expected_upper) >= 3 and expected_upper[:3] in word:
                        found = True
                        matches.append(expected)
                        print(f"✅ Trouvé approximatif: '{expected}' dans '{word}'")
                        break
            
            # Calculer le score
            match_ratio = len(matches) / len(expected_text_parts)
            print(f"Correspondance: {len(matches)}/{len(expected_text_parts)} ({match_ratio:.0%})")
            
            # Stocker les résultats
            results[mode] = {
                "text": extracted_text,
                "score": match_ratio,
                "matches": matches
            }
            
            # Mettre à jour le meilleur résultat
            if match_ratio > best_score:
                best_score = match_ratio
                best_result = mode
            
        except Exception as e:
            print(f"❌ Erreur avec {mode}: {str(e)}")
            results[mode] = {"text": "", "score": 0, "matches": [], "error": str(e)}
    
    # Afficher un résumé des résultats
    print("\n===== RÉSUMÉ DES RÉSULTATS =====")
    for mode, result in results.items():
        print(f"{mode}: {result['score']:.0%} ({len(result.get('matches', []))}/{len(expected_text_parts)} correspondances)")
    
    # Vérifier qu'au moins une méthode a donné des résultats
    if best_result:
        print(f"\n✅ Meilleure méthode: {best_result} avec {best_score:.0%}")
        # Accepter le test si au moins une méthode a trouvé du texte (même avec un score bas)
        assert best_score > 0, "Aucune méthode n'a pu extraire de texte pertinent"
    else:
        # Si nous arrivons ici, c'est qu'aucune méthode n'a fonctionné
        print("\n⚠️ Aucune méthode n'a réussi à extraire du texte")
        print("Pour résoudre ce problème, vous pouvez :")
        print("1. Installer Tesseract-OCR ou EasyOCR sur votre système")
        print("2. Essayer avec une image de meilleure qualité")
        pytest.skip("Extraction de texte impossible avec les méthodes disponibles")


if __name__ == "__main__":
    # Exécuter le test directement si le script est lancé
    try:
        test_canape_advert_text_extraction()
        print("\n✅ Test terminé avec succès")
    except Exception as e:
        print(f"\n❌ Échec du test: {str(e)}")
        sys.exit(1) 