import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np


class ModelVisualizer:
    def plot_forecasts(self, daily_data, forecasts):
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=("Daily Inspection Volume", "Daily Revenue"),
            vertical_spacing=0.1,
        )
        # Volume
        fig.add_trace(
            go.Scatter(
                x=daily_data["DATE"],
                y=daily_data["N° PV"],
                name="Actual Volume",
                mode="markers+lines",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=forecasts["volume"]["ds"],
                y=forecasts["volume"]["yhat"],
                name="Predicted Volume",
                mode="lines",
                line=dict(dash="dash"),
            ),
            row=1,
            col=1,
        )
        # Revenue
        fig.add_trace(
            go.Scatter(
                x=daily_data["DATE"],
                y=daily_data["PTTC"],
                name="Actual Revenue",
                mode="markers+lines",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=forecasts["revenue"]["ds"],
                y=forecasts["revenue"]["yhat"],
                name="Predicted Revenue",
                mode="lines",
                line=dict(dash="dash"),
            ),
            row=2,
            col=1,
        )
        fig.update_layout(
            height=700, title_text="PV Autofill Forecasting Models", showlegend=True
        )
        return fig

    def create_enhanced_dashboard(
        self, enhanced_model, train_data, test_data, enhanced_forecasts
    ):
        """Crée un dashboard amélioré avec données train/test"""

        # Créer un dashboard avec 6 sous-graphiques
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=(
                "Volume Hebdomadaire - Train vs Test",
                "Revenu Hebdomadaire - Train vs Test",
                "Régresseurs Externes - Volume",
                "Régresseurs Externes - Revenu",
                "Analyse des Résidus - Volume (Test)",
                "Analyse des Résidus - Revenu (Test)",
            ),
            vertical_spacing=0.08,
            horizontal_spacing=0.1,
        )

        # 1. Volume hebdomadaire - Train et Test
        # Données d'entraînement
        fig.add_trace(
            go.Scatter(
                x=train_data["DATE"],
                y=train_data["N° PV"],
                name="Volume Train",
                mode="markers+lines",
                marker=dict(size=6, color="blue"),
                opacity=0.7,
            ),
            row=1,
            col=1,
        )

        # Données de test
        fig.add_trace(
            go.Scatter(
                x=test_data["DATE"],
                y=test_data["N° PV"],
                name="Volume Test",
                mode="markers+lines",
                marker=dict(size=8, color="red"),
                line=dict(width=2),
            ),
            row=1,
            col=1,
        )

        if "volume" in enhanced_forecasts:
            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["volume"]["ds"],
                    y=enhanced_forecasts["volume"]["yhat"],
                    name="Volume Prédit (Test)",
                    mode="lines",
                    line=dict(dash="dash", color="orange", width=2),
                ),
                row=1,
                col=1,
            )

            # Intervalle de confiance pour le volume
            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["volume"]["ds"],
                    y=enhanced_forecasts["volume"]["yhat_upper"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["volume"]["ds"],
                    y=enhanced_forecasts["volume"]["yhat_lower"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(255,165,0,0.1)",
                    name="Intervalle de Confiance",
                ),
                row=1,
                col=1,
            )

        # 2. Revenu hebdomadaire - Train et Test
        # Données d'entraînement
        fig.add_trace(
            go.Scatter(
                x=train_data["DATE"],
                y=train_data["PTTC"],
                name="Revenu Train",
                mode="markers+lines",
                marker=dict(size=6, color="green"),
                opacity=0.7,
            ),
            row=1,
            col=2,
        )

        # Données de test
        fig.add_trace(
            go.Scatter(
                x=test_data["DATE"],
                y=test_data["PTTC"],
                name="Revenu Test",
                mode="markers+lines",
                marker=dict(size=8, color="purple"),
                line=dict(width=2),
            ),
            row=1,
            col=2,
        )

        if "revenue" in enhanced_forecasts:
            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["revenue"]["ds"],
                    y=enhanced_forecasts["revenue"]["yhat"],
                    name="Revenu Prédit (Test)",
                    mode="lines",
                    line=dict(dash="dash", color="brown", width=2),
                ),
                row=1,
                col=2,
            )

            # Intervalle de confiance pour le revenu
            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["revenue"]["ds"],
                    y=enhanced_forecasts["revenue"]["yhat_upper"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                ),
                row=1,
                col=2,
            )

            fig.add_trace(
                go.Scatter(
                    x=enhanced_forecasts["revenue"]["ds"],
                    y=enhanced_forecasts["revenue"]["yhat_lower"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(165,42,42,0.1)",
                    name="Intervalle de Confiance",
                ),
                row=1,
                col=2,
            )

        # 3. Régresseurs externes - Volume (sur train)
        if "day_of_week" in train_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_data["DATE"],
                    y=train_data["day_of_week"],
                    name="Jour de la Semaine (Train)",
                    mode="lines",
                    line=dict(color="purple"),
                ),
                row=2,
                col=1,
            )

        if "is_holiday" in train_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_data["DATE"],
                    y=train_data["is_holiday"] * 10,  # Multiplier pour visibilité
                    name="Jours Fériés (x10)",
                    mode="markers",
                    marker=dict(size=8, color="red"),
                ),
                row=2,
                col=1,
            )

        # 4. Régresseurs externes - Revenu (sur train)
        if "month" in train_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_data["DATE"],
                    y=train_data["month"],
                    name="Mois (Train)",
                    mode="lines",
                    line=dict(color="brown"),
                ),
                row=2,
                col=2,
            )

        if "is_weekend" in train_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_data["DATE"],
                    y=train_data["is_weekend"] * 5,  # Multiplier pour visibilité
                    name="Week-end (x5)",
                    mode="markers",
                    marker=dict(size=6, color="orange"),
                ),
                row=2,
                col=2,
            )

        # 5. Analyse des résidus - Volume (sur test uniquement)
        if "volume" in enhanced_forecasts:
            # Calculer les résidus pour le volume sur les données de test
            actual_volume = test_data["N° PV"].values
            predicted_volume = enhanced_forecasts["volume"]["yhat"][
                : len(actual_volume)
            ].values
            residuals_volume = actual_volume - predicted_volume

            fig.add_trace(
                go.Scatter(
                    x=test_data["DATE"],
                    y=residuals_volume,
                    name="Résidus Volume (Test)",
                    mode="markers+lines",
                    marker=dict(size=6, color="red"),
                ),
                row=3,
                col=1,
            )

            # Ligne de référence zéro
            fig.add_trace(
                go.Scatter(
                    x=test_data["DATE"],
                    y=[0] * len(test_data),
                    name="Référence",
                    mode="lines",
                    line=dict(dash="dot", color="gray"),
                ),
                row=3,
                col=1,
            )

        # 6. Analyse des résidus - Revenu (sur test uniquement)
        if "revenue" in enhanced_forecasts:
            # Calculer les résidus pour le revenu sur les données de test
            actual_revenue = test_data["PTTC"].values
            predicted_revenue = enhanced_forecasts["revenue"]["yhat"][
                : len(actual_revenue)
            ].values
            residuals_revenue = actual_revenue - predicted_revenue

            fig.add_trace(
                go.Scatter(
                    x=test_data["DATE"],
                    y=residuals_revenue,
                    name="Résidus Revenu (Test)",
                    mode="markers+lines",
                    marker=dict(size=6, color="purple"),
                ),
                row=3,
                col=2,
            )

            # Ligne de référence zéro
            fig.add_trace(
                go.Scatter(
                    x=test_data["DATE"],
                    y=[0] * len(test_data),
                    name="Référence",
                    mode="lines",
                    line=dict(dash="dot", color="gray"),
                ),
                row=3,
                col=2,
            )

        # Mise à jour du layout
        fig.update_layout(
            height=1200,
            title_text="Dashboard Amélioré - Modèles Prophet avec Split Train/Test",
            showlegend=True,
            template="plotly_white",
        )

        # Mise à jour des axes
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=3, col=2)

        fig.update_yaxes(title_text="Volume", row=1, col=1)
        fig.update_yaxes(title_text="Revenu (FCFA)", row=1, col=2)
        fig.update_yaxes(title_text="Régresseurs", row=2, col=1)
        fig.update_yaxes(title_text="Régresseurs", row=2, col=2)
        fig.update_yaxes(title_text="Résidus", row=3, col=1)
        fig.update_yaxes(title_text="Résidus", row=3, col=2)

        return fig

    def create_optimized_dashboard(
        self, optimized_model, train_daily, test_daily, optimized_forecasts
    ):
        """Crée un dashboard optimisé avec données quotidiennes train/test"""

        # Créer un dashboard avec 6 sous-graphiques
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=(
                "Volume Quotidien - Train vs Test",
                "Revenu Quotidien - Train vs Test",
                "Régresseurs Externes - Volume",
                "Régresseurs Externes - Revenu",
                "Analyse des Résidus - Volume (Test)",
                "Analyse des Résidus - Revenu (Test)",
            ),
            vertical_spacing=0.08,
            horizontal_spacing=0.1,
        )

        # 1. Volume quotidien - Train et Test
        # Données d'entraînement
        fig.add_trace(
            go.Scatter(
                x=train_daily["DATE"],
                y=train_daily["N° PV"],
                name="Volume Train",
                mode="markers+lines",
                marker=dict(size=4, color="blue"),
                opacity=0.7,
            ),
            row=1,
            col=1,
        )

        # Données de test
        fig.add_trace(
            go.Scatter(
                x=test_daily["DATE"],
                y=test_daily["N° PV"],
                name="Volume Test",
                mode="markers+lines",
                marker=dict(size=6, color="red"),
                line=dict(width=2),
            ),
            row=1,
            col=1,
        )

        if "volume" in optimized_forecasts:
            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["volume"]["ds"],
                    y=optimized_forecasts["volume"]["yhat"],
                    name="Volume Prédit (Test)",
                    mode="lines",
                    line=dict(dash="dash", color="orange", width=2),
                ),
                row=1,
                col=1,
            )

            # Intervalle de confiance pour le volume
            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["volume"]["ds"],
                    y=optimized_forecasts["volume"]["yhat_upper"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["volume"]["ds"],
                    y=optimized_forecasts["volume"]["yhat_lower"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(255,165,0,0.1)",
                    name="Intervalle de Confiance",
                ),
                row=1,
                col=1,
            )

        # 2. Revenu quotidien - Train et Test
        # Données d'entraînement
        fig.add_trace(
            go.Scatter(
                x=train_daily["DATE"],
                y=train_daily["PTTC"],
                name="Revenu Train",
                mode="markers+lines",
                marker=dict(size=4, color="green"),
                opacity=0.7,
            ),
            row=1,
            col=2,
        )

        # Données de test
        fig.add_trace(
            go.Scatter(
                x=test_daily["DATE"],
                y=test_daily["PTTC"],
                name="Revenu Test",
                mode="markers+lines",
                marker=dict(size=6, color="purple"),
                line=dict(width=2),
            ),
            row=1,
            col=2,
        )

        if "revenue" in optimized_forecasts:
            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["revenue"]["ds"],
                    y=optimized_forecasts["revenue"]["yhat"],
                    name="Revenu Prédit (Test)",
                    mode="lines",
                    line=dict(dash="dash", color="brown", width=2),
                ),
                row=1,
                col=2,
            )

            # Intervalle de confiance pour le revenu
            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["revenue"]["ds"],
                    y=optimized_forecasts["revenue"]["yhat_upper"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                ),
                row=1,
                col=2,
            )

            fig.add_trace(
                go.Scatter(
                    x=optimized_forecasts["revenue"]["ds"],
                    y=optimized_forecasts["revenue"]["yhat_lower"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(165,42,42,0.1)",
                    name="Intervalle de Confiance",
                ),
                row=1,
                col=2,
            )

        # 3. Régresseurs externes - Volume (sur train)
        if "day_of_week" in train_daily.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_daily["DATE"],
                    y=train_daily["day_of_week"],
                    name="Jour de la Semaine (Train)",
                    mode="lines",
                    line=dict(color="purple"),
                ),
                row=2,
                col=1,
            )

        if "is_holiday" in train_daily.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_daily["DATE"],
                    y=train_daily["is_holiday"] * 10,  # Multiplier pour visibilité
                    name="Jours Fériés (x10)",
                    mode="markers",
                    marker=dict(size=6, color="red"),
                ),
                row=2,
                col=1,
            )

        # 4. Régresseurs externes - Revenu (sur train)
        if "month" in train_daily.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_daily["DATE"],
                    y=train_daily["month"],
                    name="Mois (Train)",
                    mode="lines",
                    line=dict(color="brown"),
                ),
                row=2,
                col=2,
            )

        if "is_weekend" in train_daily.columns:
            fig.add_trace(
                go.Scatter(
                    x=train_daily["DATE"],
                    y=train_daily["is_weekend"] * 5,  # Multiplier pour visibilité
                    name="Week-end (x5)",
                    mode="markers",
                    marker=dict(size=4, color="orange"),
                ),
                row=2,
                col=2,
            )

        # 5. Analyse des résidus - Volume (sur test uniquement)
        if "volume" in optimized_forecasts:
            # Calculer les résidus pour le volume sur les données de test
            actual_volume = test_daily["N° PV"].values
            predicted_volume = optimized_forecasts["volume"]["yhat"][
                : len(actual_volume)
            ].values
            residuals_volume = actual_volume - predicted_volume

            fig.add_trace(
                go.Scatter(
                    x=test_daily["DATE"],
                    y=residuals_volume,
                    name="Résidus Volume (Test)",
                    mode="markers+lines",
                    marker=dict(size=4, color="red"),
                ),
                row=3,
                col=1,
            )

            # Ligne de référence zéro
            fig.add_trace(
                go.Scatter(
                    x=test_daily["DATE"],
                    y=[0] * len(test_daily),
                    name="Référence",
                    mode="lines",
                    line=dict(dash="dot", color="gray"),
                ),
                row=3,
                col=1,
            )

        # 6. Analyse des résidus - Revenu (sur test uniquement)
        if "revenue" in optimized_forecasts:
            # Calculer les résidus pour le revenu sur les données de test
            actual_revenue = test_daily["PTTC"].values
            predicted_revenue = optimized_forecasts["revenue"]["yhat"][
                : len(actual_revenue)
            ].values
            residuals_revenue = actual_revenue - predicted_revenue

            fig.add_trace(
                go.Scatter(
                    x=test_daily["DATE"],
                    y=residuals_revenue,
                    name="Résidus Revenu (Test)",
                    mode="markers+lines",
                    marker=dict(size=4, color="purple"),
                ),
                row=3,
                col=2,
            )

            # Ligne de référence zéro
            fig.add_trace(
                go.Scatter(
                    x=test_daily["DATE"],
                    y=[0] * len(test_daily),
                    name="Référence",
                    mode="lines",
                    line=dict(dash="dot", color="gray"),
                ),
                row=3,
                col=2,
            )

        # Mise à jour du layout
        fig.update_layout(
            height=1200,
            title_text="Dashboard Optimisé - Modèles Prophet Quotidiens avec Régresseurs Simplifiés",
            showlegend=True,
            template="plotly_white",
        )

        # Mise à jour des axes
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=3, col=2)

        fig.update_yaxes(title_text="Volume", row=1, col=1)
        fig.update_yaxes(title_text="Revenu (FCFA)", row=1, col=2)
        fig.update_yaxes(title_text="Régresseurs", row=2, col=1)
        fig.update_yaxes(title_text="Régresseurs", row=2, col=2)
        fig.update_yaxes(title_text="Résidus", row=3, col=1)
        fig.update_yaxes(title_text="Résidus", row=3, col=2)

        return fig
