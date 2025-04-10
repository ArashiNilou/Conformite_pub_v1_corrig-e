#!/usr/bin/env python3
"""
Script pour exécuter les tests d'extraction de texte
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_specific_test(test_file: str, verbose: bool = False) -> bool:
    """
    Exécute un test spécifique
    
    Args:
        test_file: Chemin vers le fichier de test
        verbose: Afficher les logs détaillés
        
    Returns:
        bool: True si le test a réussi, False sinon
    """
    print(f"\n🧪 Exécution du test: {test_file}")
    
    cmd = ["python", test_file]
    if verbose:
        print(f"Commande: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        success = result.returncode == 0
        
        if success:
            print(f"✅ Test {test_file} réussi")
        else:
            print(f"❌ Test {test_file} échoué (code {result.returncode})")
            
        return success
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du test {test_file}: {str(e)}")
        return False


def run_pytest(test_dir: str, verbose: bool = False) -> bool:
    """
    Exécute tous les tests avec pytest
    
    Args:
        test_dir: Répertoire des tests
        verbose: Afficher les logs détaillés
        
    Returns:
        bool: True si tous les tests ont réussi, False sinon
    """
    print(f"\n🧪 Exécution des tests avec pytest dans {test_dir}")
    
    cmd = ["pytest", "-xvs", test_dir] if verbose else ["pytest", test_dir]
    
    try:
        result = subprocess.run(cmd, check=False)
        success = result.returncode == 0
        
        if success:
            print("✅ Tous les tests ont réussi")
        else:
            print(f"❌ Certains tests ont échoué (code {result.returncode})")
            
        return success
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests: {str(e)}")
        return False


def run_all_tests(verbose: bool = False) -> int:
    """
    Exécute tous les tests d'extraction de texte
    
    Args:
        verbose: Afficher les logs détaillés
        
    Returns:
        int: Code de retour (0 si succès, 1 sinon)
    """
    test_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Répertoire des tests: {test_dir}")
    
    # Test spécifique pour la publicité du canapé
    canape_test = os.path.join(test_dir, "test_canape_advert.py")
    canape_test_success = False
    
    if os.path.exists(canape_test):
        canape_test_success = run_specific_test(canape_test, verbose)
    else:
        print(f"⚠️ Test spécifique non trouvé: {canape_test}")
    
    # Exécuter tous les tests avec pytest
    pytest_success = run_pytest(test_dir, verbose)
    
    # Résumé
    print("\n=== Résumé des tests ===")
    if os.path.exists(canape_test):
        print(f"Test publicité canapé: {'✅' if canape_test_success else '❌'}")
    print(f"Tests pytest: {'✅' if pytest_success else '❌'}")
    
    # Retourner le code de sortie
    if (os.path.exists(canape_test) and not canape_test_success) or not pytest_success:
        return 1
    return 0


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Exécute les tests d'extraction de texte")
    parser.add_argument("-v", "--verbose", action="store_true", help="Afficher les logs détaillés")
    parser.add_argument("--canape", action="store_true", help="Exécuter uniquement le test de la publicité canapé")
    parser.add_argument("--pytest", action="store_true", help="Exécuter uniquement les tests pytest")
    
    args = parser.parse_args()
    
    # Si aucune option n'est spécifiée, exécuter tous les tests
    if not (args.canape or args.pytest):
        return run_all_tests(args.verbose)
    
    success = True
    
    # Exécuter le test spécifique de la publicité canapé
    if args.canape:
        test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_canape_advert.py")
        if os.path.exists(test_file):
            success = run_specific_test(test_file, args.verbose) and success
        else:
            print(f"⚠️ Test spécifique non trouvé: {test_file}")
            success = False
    
    # Exécuter les tests pytest
    if args.pytest:
        test_dir = os.path.dirname(os.path.abspath(__file__))
        success = run_pytest(test_dir, args.verbose) and success
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 