"""
Configuration pour les tests pytest
"""

import os
import sys
import pytest
from pathlib import Path

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def pytest_sessionstart(session):
    """
    Appelé avant l'exécution des tests
    """
    print("\n🔍 Démarrage des tests d'extraction de texte")
    
    # Vérifier la présence de l'image de test
    test_image = Path("/home/dino.lakisic/Bureau/legalvision-ReAct_V2/outputs/20250305/V2 MANQUE MENTION 2606978200/image_101039.png")
    if test_image.exists():
        print(f"✅ Image de test trouvée: {test_image.absolute()}")
    else:
        print("⚠️ Image de test 'image_101039.png' non trouvée dans le répertoire courant")
        
        # Chercher l'image ailleurs
        found_images = list(Path(".").glob("**/image_101039.png"))
        if found_images:
            print(f"🔍 Image trouvée à: {found_images[0].absolute()}")
        else:
            print("❌ Image de test non trouvée dans le projet") 