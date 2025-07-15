import pandas as pd
import numpy as np
from prophet import Prophet
import logging
import holidays


class EnhancedPVProphetModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.extra_regressors = []
        self.cameroon_holidays = self._get_cameroon_holidays()

    def _get_cameroon_holidays(self):
        """Récupère les jours fériés du Cameroun"""
        cameroon_holidays = holidays.Cameroon()
        return cameroon_holidays

    def prepare_weekly_data(self, df):
        """Agrège les données par semaine pour réduire le bruit quotidien"""
        # Convertir DATE en datetime
        df["DATE"] = pd.to_datetime(df["DATE"], format="%d/%m/%Y")

        # Créer une colonne semaine
        df["WEEK"] = df["DATE"].dt.to_period("W")

        # Agrégation hebdomadaire
        weekly_data = (
            df.groupby("WEEK")
            .agg(
                {
                    "N° PV": "count",
                    "PTTC": "sum",
                    "pht": "sum",
                    "TVA": "sum",
                    "COUPON": "sum",
                }
            )
            .reset_index()
        )

        # Convertir la période en date (début de semaine)
        weekly_data["DATE"] = weekly_data["WEEK"].dt.start_time
        weekly_data = weekly_data.drop("WEEK", axis=1)

        return weekly_data

    def split_data_70_30(self, weekly_data):
        """Split les données 70% train, 30% test"""
        # Trier par date
        weekly_data = weekly_data.sort_values("DATE").reset_index(drop=True)

        # Calculer l'index de split (70% pour train)
        split_index = int(len(weekly_data) * 0.7)

        train_data = weekly_data.iloc[:split_index].copy()
        test_data = weekly_data.iloc[split_index:].copy()

        print(f"📊 Split des données:")
        print(
            f"  Train: {len(train_data)} semaines ({train_data['DATE'].min()} à {train_data['DATE'].max()})"
        )
        print(
            f"  Test:  {len(test_data)} semaines ({test_data['DATE'].min()} à {test_data['DATE'].max()})"
        )

        return train_data, test_data

    def add_external_regressors(self, data):
        """Ajoute des régresseurs externes pour améliorer les prévisions"""
        # Jours de la semaine (0=Monday, 6=Sunday)
        data["day_of_week"] = data["DATE"].dt.dayofweek

        # Mois (1-12)
        data["month"] = data["DATE"].dt.month

        # Trimestre (1-4)
        data["quarter"] = data["DATE"].dt.quarter

        # Jours fériés du Cameroun
        data["is_holiday"] = data["DATE"].apply(
            lambda x: 1 if x in self.cameroon_holidays else 0
        )

        # Week-end (samedi et dimanche)
        data["is_weekend"] = data["DATE"].dt.dayofweek.isin([5, 6]).astype(int)

        # Saisonnalité (période de l'année)
        data["day_of_year"] = data["DATE"].dt.dayofyear

        # Tendance temporelle
        data["days_since_start"] = (data["DATE"] - data["DATE"].min()).dt.days

        return data

    def log_transform_revenue(self, data):
        """Applique une transformation logarithmique au revenu pour stabiliser la variance"""
        data["PTTC_log"] = np.log1p(data["PTTC"])  # log1p pour éviter log(0)
        return data

    def create_enhanced_model(self, data, target_col, model_name, is_revenue=False):
        """Crée un modèle Prophet amélioré avec hyperparamètres optimisés"""

        # Préparer les données Prophet
        prophet_data = data[["DATE", target_col]].copy()
        prophet_data.columns = ["ds", "y"]

        # Paramètres optimisés selon le type de modèle
        if model_name == "volume":
            # Modèle pour le volume (comptage) - mode additif
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode="additive",
                mcmc_samples=500,  # Plus de chaînes pour un entraînement plus robuste
                interval_width=0.95,
                changepoint_prior_scale=0.1,  # Plus flexible pour les changements de tendance
                seasonality_prior_scale=15.0,  # Priorité sur la saisonnalité
                holidays_prior_scale=10.0,
            )
        else:
            # Modèle pour le revenu - mode multiplicatif avec transformation log
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode="multiplicative",
                mcmc_samples=500,
                interval_width=0.95,
                changepoint_prior_scale=0.05,  # Moins flexible pour le revenu
                seasonality_prior_scale=10.0,
                holidays_prior_scale=10.0,
            )

        # Ajouter les régresseurs externes
        regressor_cols = [
            "day_of_week",
            "month",
            "quarter",
            "is_holiday",
            "is_weekend",
            "day_of_year",
            "days_since_start",
        ]

        for reg in regressor_cols:
            if reg in data.columns:
                model.add_regressor(reg)
                prophet_data[reg] = data[reg].values

        # Ajouter les jours fériés du Cameroun
        model.add_country_holidays(country_name="CM")

        # Entraîner le modèle
        model.fit(prophet_data)
        self.models[model_name] = model

        return model

    def train_enhanced_models(self, df):
        """Entraîne les modèles améliorés avec agrégation hebdomadaire et split 70/30"""
        print("📊 Préparation des données avec agrégation hebdomadaire...")

        # Agrégation hebdomadaire
        weekly_data = self.prepare_weekly_data(df)

        # Split 70/30
        train_data, test_data = self.split_data_70_30(weekly_data)

        # Ajouter les régresseurs externes
        train_data = self.add_external_regressors(train_data)
        test_data = self.add_external_regressors(test_data)

        # Transformation logarithmique pour le revenu
        train_data = self.log_transform_revenue(train_data)
        test_data = self.log_transform_revenue(test_data)

        print(f"📈 Données d'entraînement: {len(train_data)} semaines")
        print(f"📈 Données de test: {len(test_data)} semaines")

        # Créer et entraîner les modèles sur les données d'entraînement
        print("🤖 Entraînement du modèle volume...")
        self.create_enhanced_model(train_data, "N° PV", "volume")

        print("💰 Entraînement du modèle revenu (avec transformation log)...")
        self.create_enhanced_model(train_data, "PTTC_log", "revenue")

        self.logger.info("Tous les modèles améliorés entraînés avec succès")
        return train_data, test_data

    def forecast_enhanced(self, test_data, periods=12):
        """Génère des prévisions avec les modèles améliorés sur les données de test"""
        forecasts = {}

        for name, model in self.models.items():
            # Créer le dataframe futur avec les données de test
            future = test_data[["DATE"]].copy()
            future.columns = ["ds"]

            # Ajouter les régresseurs externes pour les données de test
            future = self._add_future_regressors(future, test_data)

            # Prédiction
            forecast = model.predict(future)

            # Pour le revenu, transformer de log vers l'échelle originale
            if name == "revenue":
                forecast["yhat"] = np.expm1(forecast["yhat"])
                forecast["yhat_lower"] = np.expm1(forecast["yhat_lower"])
                forecast["yhat_upper"] = np.expm1(forecast["yhat_upper"])

            forecasts[name] = forecast

        return forecasts

    def _add_future_regressors(self, future, data):
        """Ajoute les régresseurs externes pour les périodes futures"""
        # Jours de la semaine
        future["day_of_week"] = future["ds"].dt.dayofweek

        # Mois
        future["month"] = future["ds"].dt.month

        # Trimestre
        future["quarter"] = future["ds"].dt.quarter

        # Jours fériés
        future["is_holiday"] = future["ds"].apply(
            lambda x: 1 if x in self.cameroon_holidays else 0
        )

        # Week-end
        future["is_weekend"] = future["ds"].dt.dayofweek.isin([5, 6]).astype(int)

        # Jour de l'année
        future["day_of_year"] = future["ds"].dt.dayofyear

        # Tendance temporelle (basée sur la date de début des données d'entraînement)
        start_date = data["DATE"].min()
        future["days_since_start"] = (future["ds"] - start_date).dt.days

        return future

    def get_model_parameters(self):
        """Retourne les paramètres des modèles pour analyse"""
        params = {}
        for name, model in self.models.items():
            params[name] = {
                "changepoint_prior_scale": model.changepoint_prior_scale,
                "seasonality_prior_scale": model.seasonality_prior_scale,
                "holidays_prior_scale": model.holidays_prior_scale,
                "seasonality_mode": model.seasonality_mode,
                "mcmc_samples": model.mcmc_samples,
            }
        return params
