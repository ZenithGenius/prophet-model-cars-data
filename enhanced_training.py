#!/usr/bin/env python3
"""
Script d'entraînement amélioré pour les modèles Prophet
Compare les modèles baseline vs améliorés avec agrégation hebdomadaire,
régresseurs externes, transformation logarithmique et split 70/30.
"""

import pandas as pd
import numpy as np
import logging
import time

# Import des modules
from ai_model.enhanced_prophet_models import EnhancedPVProphetModel
from ai_model.prophet_models import PVProphetModel
from ai_model.enhanced_evaluation import EnhancedModelEvaluator
from ai_model.visualization import ModelVisualizer

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data():
    """Charge les données du CSV"""
    print("📂 Chargement des données...")
    df = pd.read_csv("dataset/dataset.csv")
    print(f"✅ {len(df)} enregistrements chargés")
    return df


def train_baseline_models(df):
    """Entraîne les modèles baseline (quotidien) avec split 70/30"""
    print("\n🔧 Entraînement des modèles BASELINE (quotidien)...")
    print("=" * 50)

    start_time = time.time()

    # Modèle baseline
    baseline_model = PVProphetModel()

    # Préparer les données quotidiennes
    daily_data = baseline_model.prepare_daily_data(df)

    # Split 70/30 pour les données quotidiennes
    daily_data = daily_data.sort_values("DATE").reset_index(drop=True)
    split_index = int(len(daily_data) * 0.7)
    train_daily = daily_data.iloc[:split_index].copy()
    test_daily = daily_data.iloc[split_index:].copy()

    print("📊 Split baseline:")
    print(
        f"  Train: {len(train_daily)} jours ({train_daily['DATE'].min()} à {train_daily['DATE'].max()})"
    )
    print(
        f"  Test:  {len(test_daily)} jours ({test_daily['DATE'].min()} à {test_daily['DATE'].max()})"
    )

    # Entraîner sur les données d'entraînement
    baseline_model.create_model(train_daily, "N° PV", "volume")
    baseline_model.create_model(train_daily, "PTTC", "revenue")

    # Générer les prévisions sur les données de test
    baseline_forecasts = {}
    for name, model in baseline_model.models.items():
        # Créer le dataframe futur avec les données de test
        future = test_daily[["DATE"]].copy()
        future.columns = ["ds"]
        forecast = model.predict(future)
        baseline_forecasts[name] = forecast

    baseline_time = time.time() - start_time
    print(f"⏱️  Temps d'entraînement baseline: {baseline_time:.2f} secondes")

    return baseline_model, train_daily, test_daily, baseline_forecasts, baseline_time


def train_enhanced_models(df):
    """Entraîne les modèles améliorés (hebdomadaire) avec split 70/30"""
    print("\n🚀 Entraînement des modèles AMÉLIORÉS (hebdomadaire)...")
    print("=" * 50)

    start_time = time.time()

    # Modèle amélioré
    enhanced_model = EnhancedPVProphetModel()
    train_data, test_data = enhanced_model.train_enhanced_models(df)

    # Générer les prévisions améliorées sur les données de test
    enhanced_forecasts = enhanced_model.forecast_enhanced(test_data, periods=12)

    enhanced_time = time.time() - start_time
    print(f"⏱️  Temps d'entraînement amélioré: {enhanced_time:.2f} secondes")

    return enhanced_model, train_data, test_data, enhanced_forecasts, enhanced_time


def evaluate_models_on_test(baseline_model, enhanced_model, test_daily, test_data):
    """Évalue les modèles sur les données de test uniquement"""
    print("\n📊 Évaluation des modèles sur les données de TEST...")
    print("=" * 50)

    evaluator = EnhancedModelEvaluator()
    all_metrics = {}

    # Évaluer les modèles baseline sur les données de test
    print("📈 Évaluation des modèles baseline sur test...")
    for model_name in ["volume", "revenue"]:
        if model_name in baseline_model.models:
            # Utiliser les données de test
            actual_data = test_daily[
                ["DATE", "N° PV" if model_name == "volume" else "PTTC"]
            ].copy()
            actual_data.columns = ["ds", "y"]

            # Prédictions sur les données de test
            forecast_data = baseline_model.models[model_name].predict(
                actual_data[["ds"]]
            )

            metrics, _ = evaluator.evaluate_weekly_forecasts(
                actual_data, forecast_data, f"baseline_{model_name}_test"
            )
            all_metrics[f"baseline_{model_name}_test"] = metrics

    # Évaluer les modèles améliorés sur les données de test
    print("📈 Évaluation des modèles améliorés sur test...")
    for model_name in ["volume", "revenue"]:
        if model_name in enhanced_model.models:
            # Utiliser les données de test
            target_col = "N° PV" if model_name == "volume" else "PTTC_log"
            actual_data = test_data[["DATE", target_col]].copy()
            actual_data.columns = ["ds", "y"]

            # Créer le DataFrame futur avec les régresseurs externes
            future = test_data[["DATE"]].copy()
            future.columns = ["ds"]

            # Ajouter les régresseurs externes pour les données de test
            future = enhanced_model._add_future_regressors(future, test_data)

            # Prédictions sur les données de test
            forecast_data = enhanced_model.models[model_name].predict(future)

            # Pour le revenu, transformer de log vers l'échelle originale
            if model_name == "revenue":
                forecast_data["yhat"] = np.expm1(forecast_data["yhat"])
                actual_data["y"] = np.expm1(actual_data["y"])

            metrics, _ = evaluator.evaluate_weekly_forecasts(
                actual_data, forecast_data, f"enhanced_{model_name}_test"
            )
            all_metrics[f"enhanced_{model_name}_test"] = metrics

    return evaluator, all_metrics


def compare_model_performance_on_test(evaluator, all_metrics):
    """Compare les performances des modèles sur les données de test"""
    print("\n🔍 Comparaison des performances sur TEST...")
    print("=" * 50)

    # Comparer volume
    if "baseline_volume_test" in all_metrics and "enhanced_volume_test" in all_metrics:
        print("\n📊 COMPARAISON VOLUME (sur test):")
        volume_comparison = evaluator.compare_models(
            all_metrics["baseline_volume_test"], all_metrics["enhanced_volume_test"]
        )
        evaluator.print_comparison_report(volume_comparison)

    # Comparer revenu
    if (
        "baseline_revenue_test" in all_metrics
        and "enhanced_revenue_test" in all_metrics
    ):
        print("\n💰 COMPARAISON REVENU (sur test):")
        revenue_comparison = evaluator.compare_models(
            all_metrics["baseline_revenue_test"], all_metrics["enhanced_revenue_test"]
        )
        evaluator.print_comparison_report(revenue_comparison)


def create_enhanced_dashboard(
    enhanced_model, train_data, test_data, enhanced_forecasts
):
    """Crée un dashboard amélioré avec données train/test"""
    print("\n📊 Création du dashboard amélioré...")
    print("=" * 50)

    visualizer = ModelVisualizer()

    # Créer le dashboard avec les données train/test
    dashboard = visualizer.create_enhanced_dashboard(
        enhanced_model, train_data, test_data, enhanced_forecasts
    )

    # Sauvegarder le dashboard
    dashboard.write_html("enhanced_forecast_dashboard.html")
    print("✅ Dashboard amélioré sauvegardé: enhanced_forecast_dashboard.html")

    return dashboard


def print_model_parameters(enhanced_model):
    """Affiche les paramètres des modèles améliorés"""
    print("\n⚙️  Paramètres des modèles améliorés:")
    print("=" * 50)

    params = enhanced_model.get_model_parameters()
    for model_name, param_dict in params.items():
        print(f"\n{model_name.upper()}:")
        for param, value in param_dict.items():
            print(f"  {param}: {value}")


def main():
    """Fonction principale"""
    print("🚀 ENTRAÎNEMENT AMÉLIORÉ DES MODÈLES PROPHET")
    print("=" * 60)
    print("Comparaison Baseline vs Amélioré avec Split 70/30")
    print("=" * 60)

    # Charger les données
    df = load_data()

    # Entraîner les modèles baseline
    baseline_model, train_daily, test_daily, baseline_forecasts, baseline_time = (
        train_baseline_models(df)
    )

    # Entraîner les modèles améliorés
    enhanced_model, train_data, test_data, enhanced_forecasts, enhanced_time = (
        train_enhanced_models(df)
    )

    # Évaluer les modèles sur les données de test
    evaluator, all_metrics = evaluate_models_on_test(
        baseline_model, enhanced_model, test_daily, test_data
    )

    # Comparer les performances sur test
    compare_model_performance_on_test(evaluator, all_metrics)

    # Afficher les paramètres des modèles améliorés
    print_model_parameters(enhanced_model)

    # Créer le dashboard amélioré
    dashboard = create_enhanced_dashboard(
        enhanced_model, train_data, test_data, enhanced_forecasts
    )

    # Résumé final
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ FINAL")
    print("=" * 60)
    print(f"⏱️  Temps baseline: {baseline_time:.2f}s")
    print(f"⏱️  Temps amélioré: {enhanced_time:.2f}s")
    print(
        f"📈 Amélioration temps: {((baseline_time - enhanced_time) / baseline_time * 100):.1f}%"
    )
    print(f"📊 Données train baseline: {len(train_daily)} jours")
    print(f"📊 Données test baseline: {len(test_daily)} jours")
    print(f"📊 Données train amélioré: {len(train_data)} semaines")
    print(f"📊 Données test amélioré: {len(test_data)} semaines")
    print("🎯 Dashboard: enhanced_forecast_dashboard.html")

    # Ouvrir le dashboard
    import webbrowser

    webbrowser.open("enhanced_forecast_dashboard.html")

    print("\n✅ Entraînement amélioré terminé avec succès!")


if __name__ == "__main__":
    main()
