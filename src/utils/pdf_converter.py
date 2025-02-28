import fitz  # PyMuPDF
from pathlib import Path
import os
from datetime import datetime

def convert_pdf_to_image(pdf_path: str) -> str:
    """
    Convertit un PDF en image
    
    Args:
        pdf_path: Chemin vers le PDF
        
    Returns:
        str: Chemin vers l'image convertie
    """
    try:
        # Créer le dossier converted_images s'il n'existe pas
        output_dir = Path("converted_images")
        output_dir.mkdir(exist_ok=True)
        
        # Générer le nom du fichier de sortie
        pdf_name = Path(pdf_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{pdf_name}_{timestamp}.jpg"
        
        # Ouvrir le PDF
        pdf = fitz.open(pdf_path)
        
        # Convertir la première page en image
        page = pdf[0]
        pix = page.get_pixmap()
        
        # Sauvegarder l'image
        pix.save(str(output_path))
        print(f"✅ PDF converti en image : {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion du PDF : {str(e)}")
        raise
    finally:
        if 'pdf' in locals():
            pdf.close() 