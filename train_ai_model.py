#!/usr/bin/env python3
"""
Script d'entraînement du modèle d'IA avec Prophet
Utilise le dataset final avec les coupons et PTTC recalculés
"""

import pandas as pd
from pathlib import Path
import sys
import os

# Ajouter le dossier ai_model au path
sys.path.append("ai_model")

from ai_model.prophet_models import PVProphetModel
from ai_model.model_evaluation import ModelEvaluator
from ai_model.visualization import ModelVisualizer


def main():
    """Fonction principale d'entraînement"""

    print("🚀 Démarrage de l'entraînement du modèle d'IA avec Prophet")
    print("=" * 60)

    # 1. Charger les données
    csv_path = "dataset/dataset.csv"
    if not Path(csv_path).exists():
        print(f"❌ Fichier CSV non trouvé: {csv_path}")
        return
    df = pd.read_csv(csv_path)
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['DATE'])

    # 2. Entraîner les modèles Prophet (volume et revenu)
    model = PVProphetModel()
    daily_data = model.prepare_daily_data(df)
    model.train_all_models(df)

    # 3. Générer les prévisions
    forecasts = model.forecast(periods=30)

    # 4. Évaluer les modèles
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_models(daily_data, forecasts)
    print("📈 Résultats d'évaluation :")
    for name, metrics in results.items():
        print(f"  {name}: {metrics}")

    # 5. Visualisation
    visualizer = ModelVisualizer()
    fig = visualizer.plot_forecasts(daily_data, forecasts)
    os.makedirs("ai_model/results", exist_ok=True)
    fig.write_html("ai_model/results/forecast_dashboard.html")
    print("✅ Dashboard interactif sauvegardé : ai_model/results/forecast_dashboard.html")

if __name__ == "__main__":
    main()
 