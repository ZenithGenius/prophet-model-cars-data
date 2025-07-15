#!/usr/bin/env python3
"""
Script d'entraînement optimisé pour les modèles Prophet
Utilise le modèle baseline quotidien avec des améliorations ciblées :
- Régresseurs externes simplifiés
- Hyperparamètres optimisés pour éviter l'overfitting
- Split 70/30 pour évaluation honnête
"""

import pandas as pd
import logging
import time
import itertools
from prophet.diagnostics import cross_validation, performance_metrics
import numpy as np
import os
import json

# Import des modules
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


def save_best_params(params_dict, filename="best_params.json"):
    with open(filename, "w") as f:
        json.dump(params_dict, f, indent=2)
    print(f"✅ Paramètres sauvegardés dans {filename}")

def load_best_params(filename="best_params.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            params = json.load(f)
        print(f"✅ Paramètres chargés depuis {filename}")
        return params
    return None


def gridsearch_prophet_cv(train_daily, target_col, param_grid, rolling_window=3, param_file=None):
    """Effectue une gridsearch Prophet avec validation croisée et rolling mean, ou recharge les meilleurs paramètres si dispo"""
    if param_file and os.path.exists(param_file):
        best_params = load_best_params(param_file)
        print(f"Utilisation des meilleurs paramètres sauvegardés pour {target_col}: {best_params}")
        model = PVProphetModel()
        best_model = model.create_model(
            train_daily,
            target_col,
            model_name=target_col,
            changepoint_prior_scale=best_params["changepoint_prior_scale"],
            seasonality_prior_scale=best_params["seasonality_prior_scale"],
            holidays_prior_scale=best_params["holidays_prior_scale"],
            seasonality_mode=best_params["seasonality_mode"],
        )
        return best_model, best_params
    print("\n🔎 GridSearch Prophet avec validation croisée...")
    all_params = [
        dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())
    ]
    best_mape = float("inf")
    best_params = None
    best_model = None
    best_forecast = None
    for params in all_params:
        print(f"  Test: {params}")
        model = PVProphetModel()
        m = model.create_model(
            train_daily,
            target_col,
            model_name=target_col,
            changepoint_prior_scale=params["changepoint_prior_scale"],
            seasonality_prior_scale=params["seasonality_prior_scale"],
            holidays_prior_scale=params["holidays_prior_scale"],
            seasonality_mode=params["seasonality_mode"],
        )
        try:
            df_cv = cross_validation(
                m,
                initial="180 days",
                period="30 days",
                horizon="60 days",
                parallel="processes",
            )
            df_p = performance_metrics(df_cv)
            mape = df_p["mape"].mean()
            print(f"    MAPE: {mape:.4f}")
            if mape < best_mape:
                best_mape = mape
                best_params = params
                best_model = m
        except Exception as e:
            print(f"    Erreur validation croisée: {e}")
            continue
    print(f"\n✅ Meilleurs paramètres: {best_params} (MAPE={best_mape:.4f})")
    if best_params is not None and param_file:
        save_best_params(best_params, param_file)
    # Refit sur tout le train
    if best_params is not None:
        model = PVProphetModel()
        best_model = model.create_model(
            train_daily,
            target_col,
            model_name=target_col,
            changepoint_prior_scale=best_params["changepoint_prior_scale"],
            seasonality_prior_scale=best_params["seasonality_prior_scale"],
            holidays_prior_scale=best_params["holidays_prior_scale"],
            seasonality_mode=best_params["seasonality_mode"],
        )
        # Prévision sur test
        return best_model, best_params
    else:
        raise Exception("Aucun modèle valide trouvé")


def train_optimized_models_with_gridsearch(df):
    print("\n🚀 Entraînement des modèles OPTIMISÉS avec GridSearch...")
    start_time = time.time()
    daily_data = PVProphetModel().prepare_daily_data(df)
    daily_data = daily_data.sort_values("DATE").reset_index(drop=True)
    split_index = int(len(daily_data) * 0.7)
    train_daily = daily_data.iloc[:split_index].copy()
    test_daily = daily_data.iloc[split_index:].copy()
    param_grid = {
        "changepoint_prior_scale": [0.001, 0.01, 0.1, 0.5],
        "seasonality_prior_scale": [1.0, 5.0, 10.0, 20.0],
        "holidays_prior_scale": [1.0, 5.0, 10.0, 20.0],
        "seasonality_mode": ["additive", "multiplicative"],
    }
    # Volume
    print("\n🔎 GridSearch pour le volume...")
    param_file_volume = "best_params_volume.json"
    best_model_volume, best_params_volume = gridsearch_prophet_cv(
        train_daily, "N° PV", param_grid, param_file=param_file_volume
    )
    # Revenu
    print("\n🔎 GridSearch pour le revenu...")
    param_file_revenue = "best_params_revenue.json"
    best_model_revenue, best_params_revenue = gridsearch_prophet_cv(
        train_daily, "PTTC", param_grid, param_file=param_file_revenue
    )
    # Prévisions sur test
    optimized_forecasts = {}
    for name, model in zip(
        ["volume", "revenue"], [best_model_volume, best_model_revenue]
    ):
        future = test_daily[["DATE"]].copy()
        future.columns = ["ds"]
        future = PVProphetModel()._add_future_regressors(future)
        forecast = model.predict(future)
        # Rolling mean
        for col in ["yhat", "yhat_lower", "yhat_upper"]:
            forecast[col] = (
                forecast[col].rolling(window=3, min_periods=1, center=True).mean()
            )
        optimized_forecasts[name] = forecast
    optimized_time = time.time() - start_time
    print(f"⏱️  Temps d'entraînement optimisé: {optimized_time:.2f} secondes")
    return (
        (best_model_volume, best_model_revenue),
        train_daily,
        test_daily,
        optimized_forecasts,
        optimized_time,
        best_params_volume,
        best_params_revenue,
    )


def evaluate_optimized_model_single(model, test_daily, target_col):
    """Évalue un modèle Prophet unique sur les données de test"""
    print(f"\n📊 Évaluation du modèle optimisé ({target_col}) sur les données de TEST...")
    evaluator = EnhancedModelEvaluator()
    all_metrics = {}
    # Utiliser les données de test
    actual_data = test_daily[["DATE", target_col]].copy()
    actual_data.columns = ["ds", "y"]
    # Créer le DataFrame futur avec les régresseurs externes
    future = test_daily[["DATE"]].copy()
    future.columns = ["ds"]
    future = PVProphetModel()._add_future_regressors(future)
    # Prédictions sur les données de test
    forecast_data = model.predict(future)
    metrics, _ = evaluator.evaluate_weekly_forecasts(
        actual_data, forecast_data, f"optimized_{target_col}_test"
    )
    all_metrics[f"optimized_{target_col}_test"] = metrics
    return evaluator, all_metrics


def print_optimized_metrics(evaluator, all_metrics):
    """Affiche les métriques des modèles optimisés"""
    print("\n📊 MÉTRIQUES DES MODÈLES OPTIMISÉS (sur test):")
    print("=" * 60)

    for model_name, metrics in all_metrics.items():
        print(f"\n{model_name.upper()}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")


def create_optimized_dashboard(
    optimized_model, train_daily, test_daily, optimized_forecasts
):
    """Crée un dashboard optimisé avec données train/test"""
    print("\n📊 Création du dashboard optimisé...")
    print("=" * 50)

    visualizer = ModelVisualizer()

    # Créer le dashboard avec les données train/test
    dashboard = visualizer.create_optimized_dashboard(
        optimized_model, train_daily, test_daily, optimized_forecasts
    )

    # Sauvegarder le dashboard
    dashboard.write_html("optimized_forecast_dashboard.html")
    print("✅ Dashboard optimisé sauvegardé: optimized_forecast_dashboard.html")

    return dashboard


def print_model_parameters(optimized_model):
    """Affiche les paramètres des modèles optimisés"""
    print("\n⚙️  Paramètres des modèles optimisés:")
    print("=" * 50)
    # Robustesse : accepte Prophet natif ou wrapper
    if hasattr(optimized_model, 'models'):
        for name, model in optimized_model.models.items():
            print(f"\n{name.upper()}:")
            print(f"  changepoint_prior_scale: {getattr(model, 'changepoint_prior_scale', 'N/A')}")
            print(f"  seasonality_prior_scale: {getattr(model, 'seasonality_prior_scale', 'N/A')}")
            print(f"  holidays_prior_scale: {getattr(model, 'holidays_prior_scale', 'N/A')}")
            print(f"  seasonality_mode: {getattr(model, 'seasonality_mode', 'N/A')}")
            print(f"  mcmc_samples: {getattr(model, 'mcmc_samples', 'N/A')}")
    else:
        print(f"  changepoint_prior_scale: {getattr(optimized_model, 'changepoint_prior_scale', 'N/A')}")
        print(f"  seasonality_prior_scale: {getattr(optimized_model, 'seasonality_prior_scale', 'N/A')}")
        print(f"  holidays_prior_scale: {getattr(optimized_model, 'holidays_prior_scale', 'N/A')}")
        print(f"  seasonality_mode: {getattr(optimized_model, 'seasonality_mode', 'N/A')}")
        print(f"  mcmc_samples: {getattr(optimized_model, 'mcmc_samples', 'N/A')}")


def analyze_residuals_by_segment(test_daily, optimized_forecasts):
    print("\n📊 Analyse des résidus par segment:")
    for target in ["volume", "revenue"]:
        if target in optimized_forecasts:
            actual = test_daily["N° PV"] if target == "volume" else test_daily["PTTC"]
            pred = optimized_forecasts[target]["yhat"][: len(actual)]
            residuals = actual.values - pred.values
            test_daily[f"residuals_{target}"] = residuals
            print(f"\nRésidus pour {target}:")
            print(
                f"  Moyenne: {np.mean(residuals):.2f}, Écart-type: {np.std(residuals):.2f}"
            )
            # Par jour de la semaine
            test_daily["day_name"] = test_daily["DATE"].dt.day_name()
            print("  Par jour de la semaine:")
            print(test_daily.groupby("day_name")[f"residuals_{target}"].mean())
            # Par mois
            test_daily["month"] = test_daily["DATE"].dt.month_name()
            print("  Par mois:")
            print(test_daily.groupby("month")[f"residuals_{target}"].mean())
            # Par événement spécial
            for event in [
                "festi_bikutsi",
                "modaperf",
                "yaounde_en_fete",
                "marche_noel",
                "fete_nationale",
                "fete_travail",
            ]:
                test_daily[event] = test_daily["DATE"].isin(
                    [
                        pd.Timestamp("2024-11-12"),
                        pd.Timestamp("2025-11-12"),
                        pd.Timestamp("2024-11-20"),
                        pd.Timestamp("2025-11-20"),
                        pd.Timestamp("2024-12-20"),
                        pd.Timestamp("2025-12-20"),
                        pd.Timestamp("2024-12-05"),
                        pd.Timestamp("2025-12-05"),
                        pd.Timestamp("2024-05-20"),
                        pd.Timestamp("2025-05-20"),
                        pd.Timestamp("2024-05-01"),
                        pd.Timestamp("2025-05-01"),
                    ]
                )
                print(
                    f"  Moyenne des résidus pendant {event}: {test_daily.loc[test_daily[event], f'residuals_{target}'].mean()}"
                )


def main():
    """Fonction principale"""
    print("🚀 ENTRAÎNEMENT OPTIMISÉ DES MODÈLES PROPHET (GridSearch + CV)")
    print("=" * 60)
    df = load_data()
    (best_model_volume, best_model_revenue), train_daily, test_daily, optimized_forecasts, optimized_time, best_params_volume, best_params_revenue = train_optimized_models_with_gridsearch(df)
    # Analyse des résidus par segment
    analyze_residuals_by_segment(test_daily, optimized_forecasts)
    # Évaluer les modèles sur les données de test
    evaluator_v, all_metrics_v = evaluate_optimized_model_single(best_model_volume, test_daily, "N° PV")
    evaluator_r, all_metrics_r = evaluate_optimized_model_single(best_model_revenue, test_daily, "PTTC")
    # Afficher les métriques optimisées
    print_optimized_metrics(evaluator_v, all_metrics_v)
    print_optimized_metrics(evaluator_r, all_metrics_r)
    # Afficher les paramètres des modèles optimisés
    print("\nParamètres volume:")
    print_model_parameters(best_model_volume)
    print("\nParamètres revenu:")
    print_model_parameters(best_model_revenue)
    # Créer le dashboard optimisé
    dashboard = create_optimized_dashboard(
        best_model_volume, train_daily, test_daily, optimized_forecasts
    )

    # Résumé final
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ FINAL")
    print("=" * 60)
    print(f"⏱️  Temps d'entraînement: {optimized_time:.2f}s")
    print(f"📊 Données train: {len(train_daily)} jours")
    print(f"📊 Données test: {len(test_daily)} jours")
    print(f"🔧 Régresseurs: day_of_week, is_weekend, is_holiday, month")
    print(f"⚙️  Hyperparamètres: optimisés pour éviter l'overfitting")
    print("🎯 Dashboard: optimized_forecast_dashboard.html")

    # Ouvrir le dashboard
    import webbrowser

    webbrowser.open("optimized_forecast_dashboard.html")

    print("\n✅ Entraînement optimisé terminé avec succès!")


if __name__ == "__main__":
    main()
