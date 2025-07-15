import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging


class EnhancedModelEvaluator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {}

    def calculate_enhanced_metrics(self, actual, predicted, model_name):
        """Calcule des métriques d'évaluation améliorées"""
        # Métriques de base
        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)

        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        # R² (Coefficient de détermination)
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Métriques spécifiques pour les séries temporelles
        # Directional Accuracy (précision directionnelle)
        actual_diff = np.diff(actual)
        predicted_diff = np.diff(predicted)
        directional_accuracy = np.mean((actual_diff > 0) == (predicted_diff > 0)) * 100

        # Theil's U (ratio de Theil)
        theil_u = rmse / (np.sqrt(np.mean(actual**2)) + np.sqrt(np.mean(predicted**2)))

        metrics = {
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
            "R2": r2,
            "Directional_Accuracy": directional_accuracy,
            "Theil_U": theil_u,
        }

        self.metrics[model_name] = metrics
        return metrics

    def compare_models(self, baseline_metrics, enhanced_metrics):
        """Compare les performances des modèles baseline vs amélioré"""
        comparison = {}

        for metric in ["MAE", "RMSE", "MAPE", "R2", "Directional_Accuracy", "Theil_U"]:
            if metric in baseline_metrics and metric in enhanced_metrics:
                baseline_val = baseline_metrics[metric]
                enhanced_val = enhanced_metrics[metric]

                # Calculer l'amélioration (pourcentage)
                if baseline_val != 0:
                    if metric in ["MAE", "RMSE", "MAPE", "Theil_U"]:
                        # Pour ces métriques, une valeur plus basse est meilleure
                        improvement = (
                            (baseline_val - enhanced_val) / baseline_val
                        ) * 100
                    else:
                        # Pour R² et Directional_Accuracy, une valeur plus haute est meilleure
                        improvement = (
                            (enhanced_val - baseline_val) / baseline_val
                        ) * 100
                else:
                    improvement = 0

                comparison[metric] = {
                    "baseline": baseline_val,
                    "enhanced": enhanced_val,
                    "improvement_pct": improvement,
                }

        return comparison

    def print_comparison_report(self, comparison):
        """Affiche un rapport de comparaison détaillé"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT DE COMPARAISON DES MODÈLES")
        print("=" * 60)

        for metric, values in comparison.items():
            baseline = values["baseline"]
            enhanced = values["enhanced"]
            improvement = values["improvement_pct"]

            # Déterminer si c'est une amélioration
            if metric in ["MAE", "RMSE", "MAPE", "Theil_U"]:
                is_improvement = enhanced < baseline
                direction = "↓" if is_improvement else "↑"
            else:
                is_improvement = enhanced > baseline
                direction = "↑" if is_improvement else "↓"

            status = "✅ AMÉLIORATION" if is_improvement else "❌ DÉGRADATION"

            print(f"\n{metric}:")
            print(f"  Baseline: {baseline:.4f}")
            print(f"  Enhanced:  {enhanced:.4f}")
            print(f"  Amélioration: {improvement:.2f}% {direction}")
            print(f"  Status: {status}")

        # Résumé global
        improvements = [
            v["improvement_pct"]
            for v in comparison.values()
            if v["improvement_pct"] > 0
        ]
        degradations = [
            v["improvement_pct"]
            for v in comparison.values()
            if v["improvement_pct"] < 0
        ]

        print(f"\n📈 RÉSUMÉ:")
        print(f"  Métriques améliorées: {len(improvements)}")
        print(f"  Métriques dégradées: {len(degradations)}")
        if improvements:
            print(f"  Amélioration moyenne: {np.mean(improvements):.2f}%")
        if degradations:
            print(f"  Dégradation moyenne: {np.mean(degradations):.2f}%")

    def evaluate_weekly_forecasts(self, actual_data, forecast_data, model_name):
        """Évalue les prévisions hebdomadaires"""
        # Aligner les données
        merged = pd.merge(actual_data, forecast_data, on="ds", how="inner")

        # Calculer les métriques
        metrics = self.calculate_enhanced_metrics(
            merged["y"], merged["yhat"], model_name
        )

        return metrics, merged

    def generate_evaluation_summary(self, all_metrics):
        """Génère un résumé d'évaluation pour tous les modèles"""
        summary = {}

        for model_name, metrics in all_metrics.items():
            summary[model_name] = {
                "MAE": metrics.get("MAE", 0),
                "RMSE": metrics.get("RMSE", 0),
                "MAPE": metrics.get("MAPE", 0),
                "R2": metrics.get("R2", 0),
                "Directional_Accuracy": metrics.get("Directional_Accuracy", 0),
            }

        return pd.DataFrame(summary).T
