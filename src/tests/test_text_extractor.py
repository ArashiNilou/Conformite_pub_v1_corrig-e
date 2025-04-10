import pytest
import os
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_extractor import TextExtractor


class TestTextExtractor:
    """Tests pour l'extracteur de texte"""
    
    @pytest.fixture
    def text_extractor(self):
        """Fixture pour l'extracteur de texte"""
        return TextExtractor()
    
    @pytest.fixture
    def sample_image_path(self):
        """Crée une image temporaire pour les tests"""
        # Créer un répertoire temporaire
        temp_dir = tempfile.mkdtemp()
        
        # Chemin pour une image de test
        temp_img_path = os.path.join(temp_dir, "/home/dino.lakisic/Bureau/legalvision-ReAct_V2/outputs/20250305/V2 MANQUE MENTION 2606978200/image_101039.png")
        
        # Créer une image simple avec du texte (à faire programmatiquement dans un vrai test)
        img = Image.new('RGB', (500, 200), color=(255, 255, 255))
        img.save(temp_img_path)
        
        yield temp_img_path
        
        # Nettoyage après le test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Crée un PDF temporaire pour les tests"""
        # Créer un répertoire temporaire
        temp_dir = tempfile.mkdtemp()
        
        # Chemin pour un PDF de test
        temp_pdf_path = os.path.join(temp_dir, "test_document.pdf")
        
        # Créer une image simple puis la convertir en PDF
        img = Image.new('RGB', (500, 200), color=(255, 255, 255))
        img.save(temp_pdf_path, "PDF")
        
        yield temp_pdf_path
        
        # Nettoyage après le test
        shutil.rmtree(temp_dir)
    
    @pytest.mark.parametrize("ocr_engine", ["tesseract", "easyocr", "tesseract_api"])
    def test_docling_extraction_with_different_engines(self, text_extractor, sample_pdf_path, ocr_engine):
        """Teste l'extraction avec différents moteurs Docling"""
        try:
            # Test avec le moteur spécifié
            extracted_text = text_extractor.extract_text_with_docling(sample_pdf_path, ocr_engine)
            
            # Vérifications basiques
            assert isinstance(extracted_text, str)
            print(f"Texte extrait avec {ocr_engine}: {extracted_text[:100]}...")
            
        except ImportError as e:
            pytest.skip(f"Moteur OCR {ocr_engine} non disponible: {str(e)}")
        except Exception as e:
            if "not installed" in str(e).lower():
                pytest.skip(f"Moteur OCR {ocr_engine} non installé: {str(e)}")
            else:
                raise
    
    def test_clean_markdown_text(self, text_extractor):
        """Teste le nettoyage du texte markdown"""
        markdown_text = """
        # Titre
        
        Voici du texte normal.
        
        ## Sous-titre
        
        - Liste item 1
        - Liste item 2
        
        ```
        Code block
        ```
        
        [Lien](https://example.com)
        
        ---
        
        Plus de texte ici.
        """
        
        cleaned_text = text_extractor._clean_markdown_text(markdown_text)
        
        # Vérifications
        assert "# Titre" not in cleaned_text
        assert "## Sous-titre" not in cleaned_text
        assert "---" not in cleaned_text
        assert "Voici du texte normal." in cleaned_text
        assert "Liste item 1" in cleaned_text
        assert "Liste item 2" in cleaned_text
        assert "Plus de texte ici." in cleaned_text
    
    def test_extraction_fallback(self, text_extractor, sample_image_path):
        """Teste que le fallback vers Docling fonctionne"""
        # Tenter d'utiliser un mode inexistant, qui devrait faire un fallback vers docling
        try:
            extracted_text = text_extractor.extract_text(sample_image_path, mode="non_existent")
            
            # Vérifications basiques
            assert isinstance(extracted_text, str)
            
        except Exception as e:
            # Si Docling n'est pas correctement installé, accepter le skip de test
            if "docling" in str(e).lower():
                pytest.skip(f"Docling n'est pas correctement installé: {str(e)}")
            else:
                raise
    
    def test_real_image_extraction(self, text_extractor):
        """
        Teste l'extraction sur une image réelle avec du texte
        Note: Cette image doit être présente dans le système de fichiers
        """
        # Chercher des images d'exemple dans le répertoire du projet
        data_dir = Path("src/data")
        if not data_dir.exists():
            pytest.skip("Répertoire de données non trouvé pour les tests sur images réelles")
        
        # Chercher une image de test
        image_files = list(data_dir.glob("*.jpg")) + list(data_dir.glob("*.png")) + list(data_dir.glob("*.pdf"))
        
        if not image_files:
            pytest.skip("Aucune image de test trouvée dans le répertoire data")
        
        test_image = str(image_files[0])
        print(f"Test sur l'image réelle: {test_image}")
        
        try:
            extracted_text = text_extractor.extract_text(test_image)
            
            # Vérifications basiques
            assert isinstance(extracted_text, str)
            print(f"Texte extrait de l'image réelle: {extracted_text[:150]}...")
            
        except Exception as e:
            if "docling" in str(e).lower() or "tesseract" in str(e).lower():
                pytest.skip(f"Problème avec l'extracteur de texte: {str(e)}")
            else:
                raise 