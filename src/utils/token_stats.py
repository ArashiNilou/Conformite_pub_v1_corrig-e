#!/usr/bin/env python3
"""
Utilitaire pour afficher et analyser les statistiques d'utilisation des tokens.

Utilisation:
    python token_stats.py --dir stats/tokens
"""

import argparse
import json
from pathlib import Path
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional


def load_stats_files(directory: str) -> List[Dict[str, Any]]:
    """
    Charge tous les fichiers de statistiques dans le répertoire spécifié.
    
    Args:
        directory: Chemin vers le répertoire contenant les fichiers de statistiques
        
    Returns:
        List[Dict]: Liste des statistiques chargées
    """
    stats_list = []
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"⚠️ Le répertoire {directory} n'existe pas ou n'est pas un répertoire.")
        return []
    
    # Parcourir tous les fichiers JSON dans le répertoire
    for file_path in sorted(dir_path.glob("*.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                stats["file"] = str(file_path)
                stats_list.append(stats)
                print(f"✅ Chargé: {file_path}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {file_path}: {str(e)}")
    
    return stats_list


def summarize_stats(stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcule un résumé des statistiques d'utilisation des tokens.
    
    Args:
        stats_list: Liste des statistiques à résumer
        
    Returns:
        Dict: Résumé des statistiques
    """
    if not stats_list:
        return {"error": "Aucune statistique disponible"}
    
    # Initialiser le résumé
    summary = {
        "total_files": len(stats_list),
        "total_prompt_tokens": sum(s.get("total_prompt_tokens", 0) for s in stats_list),
        "total_completion_tokens": sum(s.get("total_completion_tokens", 0) for s in stats_list),
        "total_tokens": sum(s.get("total_tokens", 0) for s in stats_list),
        "total_cost_usd": sum(s.get("estimated_cost_usd", 0) for s in stats_list),
        "models": {},
        "start_date": None,
        "end_date": None
    }
    
    # Agréger les données par modèle
    for stats in stats_list:
        # Mettre à jour les dates
        timestamp = stats.get("timestamp")
        if timestamp:
            date = datetime.datetime.fromisoformat(timestamp)
            if summary["start_date"] is None or date < summary["start_date"]:
                summary["start_date"] = date
            if summary["end_date"] is None or date > summary["end_date"]:
                summary["end_date"] = date
        
        # Agréger les données par modèle
        for model_name, model_stats in stats.get("models", {}).items():
            if model_name not in summary["models"]:
                summary["models"][model_name] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0,
                    "calls": 0
                }
            
            model_summary = summary["models"][model_name]
            model_summary["prompt_tokens"] += model_stats.get("prompt_tokens", 0)
            model_summary["completion_tokens"] += model_stats.get("completion_tokens", 0)
            model_summary["total_tokens"] = model_summary["prompt_tokens"] + model_summary["completion_tokens"]
            model_summary["cost"] += model_stats.get("cost", 0)
            model_summary["calls"] += model_stats.get("calls", 0)
    
    # Convertir les dates en chaînes de caractères
    if summary["start_date"]:
        summary["start_date"] = summary["start_date"].strftime("%Y-%m-%d %H:%M:%S")
    if summary["end_date"]:
        summary["end_date"] = summary["end_date"].strftime("%Y-%m-%d %H:%M:%S")
    
    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """
    Affiche un résumé des statistiques d'utilisation des tokens.
    
    Args:
        summary: Résumé des statistiques
    """
    if "error" in summary:
        print(f"⚠️ {summary['error']}")
        return
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES STATISTIQUES D'UTILISATION DES TOKENS")
    print("="*60)
    
    print(f"\n📁 Fichiers analysés: {summary['total_files']}")
    print(f"📅 Période: {summary['start_date']} - {summary['end_date']}")
    
    print("\n💰 COÛTS ET TOKENS TOTAUX")
    print("-"*60)
    print(f"  Tokens prompt:      {summary['total_prompt_tokens']:,}")
    print(f"  Tokens completion:  {summary['total_completion_tokens']:,}")
    print(f"  TOKENS TOTAUX:      {summary['total_tokens']:,}")
    print(f"  COÛT TOTAL:         ${summary['total_cost_usd']:.2f}")
    
    # Afficher les statistiques par modèle
    print("\n🤖 DÉTAIL PAR MODÈLE")
    print("-"*60)
    for model_name, model_stats in summary["models"].items():
        print(f"\n  Modèle: {model_name}")
        print(f"  Appels:              {model_stats['calls']:,}")
        print(f"  Tokens prompt:       {model_stats['prompt_tokens']:,}")
        print(f"  Tokens completion:   {model_stats['completion_tokens']:,}")
        print(f"  Tokens totaux:       {model_stats['total_tokens']:,}")
        print(f"  Coût:                ${model_stats['cost']:.2f}")
        if model_stats['calls'] > 0:
            print(f"  Moyenne par appel:   ${model_stats['cost'] / model_stats['calls']:.4f}")
    
    print("\n" + "="*60)


def generate_charts(summary: Dict[str, Any], output_dir: Optional[str] = None) -> None:
    """
    Génère des graphiques à partir des statistiques d'utilisation des tokens.
    
    Args:
        summary: Résumé des statistiques
        output_dir: Répertoire de sortie pour les graphiques (optionnel)
    """
    if "error" in summary:
        print(f"⚠️ {summary['error']}")
        return
    
    try:
        # Créer un répertoire de sortie si nécessaire
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = Path("stats/charts")
            out_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp pour les noms de fichiers
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Graphique des tokens totaux
        plt.figure(figsize=(10, 6))
        models = list(summary["models"].keys())
        prompt_tokens = [summary["models"][m]["prompt_tokens"] for m in models]
        completion_tokens = [summary["models"][m]["completion_tokens"] for m in models]
        
        plt.bar(models, prompt_tokens, label='Prompt Tokens')
        plt.bar(models, completion_tokens, label='Completion Tokens', bottom=prompt_tokens)
        
        plt.title('Utilisation de Tokens par Modèle')
        plt.xlabel('Modèle')
        plt.ylabel('Nombre de Tokens')
        plt.legend()
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        tokens_chart_path = out_dir / f"tokens_by_model_{timestamp}.png"
        plt.savefig(tokens_chart_path)
        print(f"✅ Graphique des tokens sauvegardé: {tokens_chart_path}")
        
        # Graphique des coûts
        plt.figure(figsize=(10, 6))
        costs = [summary["models"][m]["cost"] for m in models]
        
        plt.bar(models, costs)
        plt.title('Coût par Modèle')
        plt.xlabel('Modèle')
        plt.ylabel('Coût (USD)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        cost_chart_path = out_dir / f"cost_by_model_{timestamp}.png"
        plt.savefig(cost_chart_path)
        print(f"✅ Graphique des coûts sauvegardé: {cost_chart_path}")
        
        # Graphique camembert des coûts
        plt.figure(figsize=(10, 8))
        plt.pie(costs, labels=models, autopct='%1.1f%%')
        plt.title('Répartition des Coûts par Modèle')
        plt.axis('equal')
        
        pie_chart_path = out_dir / f"cost_distribution_{timestamp}.png"
        plt.savefig(pie_chart_path)
        print(f"✅ Graphique de répartition des coûts sauvegardé: {pie_chart_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des graphiques: {str(e)}")


def generate_report(summary: Dict[str, Any], output_file: Optional[str] = None) -> None:
    """
    Génère un rapport HTML à partir des statistiques d'utilisation des tokens.
    
    Args:
        summary: Résumé des statistiques
        output_file: Chemin du fichier de sortie (optionnel)
    """
    if "error" in summary:
        print(f"⚠️ {summary['error']}")
        return
    
    try:
        # Créer un répertoire de sortie si nécessaire
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = Path("stats/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            output_file = report_dir / f"token_usage_report_{timestamp}.html"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Données pour le tableau des modèles
        model_data = []
        for model_name, model_stats in summary["models"].items():
            model_data.append({
                "Modèle": model_name,
                "Appels": format(model_stats['calls'], ","),
                "Tokens Prompt": format(model_stats['prompt_tokens'], ","),
                "Tokens Completion": format(model_stats['completion_tokens'], ","),
                "Tokens Totaux": format(model_stats['total_tokens'], ","),
                "Coût (USD)": f"${model_stats['cost']:.2f}",
                "Coût Moyen/Appel": f"${model_stats['cost'] / max(1, model_stats['calls']):.4f}"
            })
        
        # Créer un DataFrame pandas pour le tableau
        df = pd.DataFrame(model_data)
        
        # Générer le HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport d'Utilisation des Tokens - {summary['start_date']} à {summary['end_date']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary p {{ margin: 5px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ text-align: left; padding: 8px; }}
                th {{ background-color: #3498db; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .highlight {{ font-weight: bold; color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>Rapport d'Utilisation des Tokens</h1>
            
            <div class="summary">
                <h2>Résumé</h2>
                <p><strong>Période:</strong> {summary['start_date']} - {summary['end_date']}</p>
                <p><strong>Fichiers analysés:</strong> {summary['total_files']}</p>
                <p><strong>Tokens totaux:</strong> {format(summary['total_tokens'], ",")}</p>
                <p class="highlight"><strong>Coût total:</strong> ${summary['total_cost_usd']:.2f}</p>
            </div>
            
            <h2>Détail par Modèle</h2>
            {df.to_html(index=False)}
            
            <div style="margin-top: 20px;">
                <p><em>Rapport généré le {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
            </div>
        </body>
        </html>
        """
        
        # Écrire le HTML dans un fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Rapport HTML sauvegardé: {output_file}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {str(e)}")


def export_csv(summary: Dict[str, Any], output_file: Optional[str] = None) -> None:
    """
    Exporte les statistiques d'utilisation des tokens au format CSV.
    
    Args:
        summary: Résumé des statistiques
        output_file: Chemin du fichier de sortie (optionnel)
    """
    if "error" in summary:
        print(f"⚠️ {summary['error']}")
        return
    
    try:
        # Créer un répertoire de sortie si nécessaire
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_dir = Path("stats/exports")
            csv_dir.mkdir(parents=True, exist_ok=True)
            output_file = csv_dir / f"token_usage_{timestamp}.csv"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Données pour le CSV
        model_data = []
        for model_name, model_stats in summary["models"].items():
            model_data.append({
                "Modèle": model_name,
                "Appels": model_stats['calls'],
                "Tokens Prompt": model_stats['prompt_tokens'],
                "Tokens Completion": model_stats['completion_tokens'],
                "Tokens Totaux": model_stats['total_tokens'],
                "Coût (USD)": model_stats['cost'],
                "Coût Moyen/Appel": model_stats['cost'] / max(1, model_stats['calls'])
            })
        
        # Créer un DataFrame pandas et exporter en CSV
        df = pd.DataFrame(model_data)
        df.to_csv(output_file, index=False)
        
        print(f"✅ Export CSV sauvegardé: {output_file}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export CSV: {str(e)}")


def parse_args():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description="Analyser et visualiser les statistiques d'utilisation des tokens")
    parser.add_argument("--dir", default="stats/tokens", help="Répertoire contenant les fichiers de statistiques")
    parser.add_argument("--report", action="store_true", help="Générer un rapport HTML")
    parser.add_argument("--charts", action="store_true", help="Générer des graphiques")
    parser.add_argument("--csv", action="store_true", help="Exporter les données au format CSV")
    parser.add_argument("--output", help="Répertoire de sortie pour les rapports et graphiques")
    
    return parser.parse_args()


def main():
    """Point d'entrée principal de l'application"""
    args = parse_args()
    
    print(f"\n🔍 Analyse des statistiques dans: {args.dir}")
    
    # Charger les fichiers de statistiques
    stats_list = load_stats_files(args.dir)
    
    if not stats_list:
        print("⚠️ Aucun fichier de statistiques trouvé.")
        return
    
    # Calculer un résumé des statistiques
    summary = summarize_stats(stats_list)
    
    # Afficher le résumé
    print_summary(summary)
    
    # Générer un rapport HTML si demandé
    if args.report:
        output_file = None
        if args.output:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(args.output) / f"token_usage_report_{timestamp}.html"
        generate_report(summary, output_file)
    
    # Générer des graphiques si demandé
    if args.charts:
        generate_charts(summary, args.output)
    
    # Exporter au format CSV si demandé
    if args.csv:
        output_file = None
        if args.output:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(args.output) / f"token_usage_{timestamp}.csv"
        export_csv(summary, output_file)
    
    print("\n✅ Analyse terminée")


if __name__ == "__main__":
    main() 