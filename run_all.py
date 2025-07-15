#!/usr/bin/env python3
"""
Script d'automatisation complet pour le projet PV Autofill
Met à jour le CSV, entraîne les modèles IA, et ouvre le dashboard
"""

import subprocess
import webbrowser
import time
from pathlib import Path
import sys


# def run_update_csv():
#     """Met à jour le CSV avec les coupons extraits des fichiers Excel"""
#     print("🔄 Étape 1: Mise à jour du CSV avec les coupons...")
#     print("=" * 50)

#     try:
#         subprocess.run(
#             ["python", "update_csv_with_coupons.py"],
#             capture_output=True,
#             text=True,
#             check=True,
#         )
#         print("✅ CSV mis à jour avec succès")
#         return True
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Erreur lors de la mise à jour du CSV: {e}")
#         print(f"Sortie d'erreur: {e.stderr}")
#         return False


def run_training():
    """Entraîne les modèles IA et génère les prévisions"""
    print("\n🤖 Étape 1: Entraînement des modèles IA...")
    print("=" * 50)

    try:
        subprocess.run(
            ["python", "train_ai_model.py"], capture_output=True, text=True, check=True
        )
        print("✅ Entraînement terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'entraînement: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False


def open_dashboard():
    """Ouvre le dashboard dans le navigateur"""
    dashboard_path = Path("ai_model/results/forecast_dashboard.html")

    if dashboard_path.exists():
        dashboard_uri = dashboard_path.absolute().as_uri()
        print(f"\n🌐 Ouverture du dashboard: {dashboard_uri}")
        try:
            webbrowser.open(dashboard_uri)
            print("✅ Dashboard ouvert dans le navigateur")
        except Exception as e:
            print(f"⚠️ Impossible d'ouvrir automatiquement le dashboard: {e}")
            print(f"Ouvre manuellement: {dashboard_path}")
    else:
        print(
            "❌ Dashboard non trouvé. Vérifiez que l'entraînement s'est bien terminé."
        )


def main():
    """Fonction principale d'automatisation"""
    print("🚀 AUTOMATISATION COMPLÈTE - PV AUTOFILL")
    print("=" * 60)

    start_time = time.time()

    # Étape 2: Entraînement IA
    if not run_training():
        print("❌ Arrêt de l'automatisation - échec de l'entraînement")
        sys.exit(1)

    # Étape 3: Ouverture du dashboard
    open_dashboard()

    # Résumé final
    end_time = time.time()
    duration = end_time - start_time

    print("\n🎉 AUTOMATISATION TERMINÉE!")
    print(f"⏱️ Durée totale: {duration:.1f} secondes")
    print("📁 Résultats disponibles dans: ai_model/results/")
    print("📊 Dashboard: ai_model/results/forecast_dashboard.html")


if __name__ == "__main__":
    main()
