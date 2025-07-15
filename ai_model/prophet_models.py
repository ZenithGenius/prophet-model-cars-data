from prophet import Prophet
import logging
import pandas as pd
import holidays
import numpy as np


class PVProphetModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.extra_regressors = []
        self.cameroon_holidays = self._get_cameroon_holidays()
        self.special_events = self._get_special_events_holidays()

    def _get_cameroon_holidays(self):
        """Récupère les jours fériés du Cameroun"""
        cameroon_holidays = holidays.Cameroon()
        return cameroon_holidays

    def _get_special_events_holidays(self):
        """Retourne un DataFrame de holidays personnalisés pour les événements spéciaux de Yaoundé"""
        # Format Prophet: columns = ['holiday', 'ds', 'lower_window', 'upper_window']
        events = [
            # Festi Bikutsi (novembre, mettons 10-15 novembre)
            {"holiday": "festi_bikutsi", "ds": "2024-11-12"},
            {"holiday": "festi_bikutsi", "ds": "2025-11-12"},
            # Modaperf (novembre, mettons 20 novembre)
            {"holiday": "modaperf", "ds": "2024-11-20"},
            {"holiday": "modaperf", "ds": "2025-11-20"},
            # Yaoundé en fête (décembre, mettons 20 décembre)
            {"holiday": "yaounde_en_fete", "ds": "2024-12-20"},
            {"holiday": "yaounde_en_fete", "ds": "2025-12-20"},
            # Marché de Noël (début décembre, mettons 5 décembre)
            {"holiday": "marche_noel", "ds": "2024-12-05"},
            {"holiday": "marche_noel", "ds": "2025-12-05"},
            # Fête Nationale (20 mai)
            {"holiday": "fete_nationale", "ds": "2024-05-20"},
            {"holiday": "fete_nationale", "ds": "2025-05-20"},
            # Fête du Travail (1er mai)
            {"holiday": "fete_travail", "ds": "2024-05-01"},
            {"holiday": "fete_travail", "ds": "2025-05-01"},
        ]
        df_events = pd.DataFrame(events)
        df_events["lower_window"] = 0
        df_events["upper_window"] = 0
        return df_events

    def prepare_daily_data(self, df):
        # Convertir DATE en datetime avec le format français
        df["DATE"] = pd.to_datetime(df["DATE"], format="%d/%m/%Y")

        daily_data = (
            df.groupby("DATE")
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

        # Ajouter des régresseurs externes simplifiés
        daily_data = self.add_simple_regressors(daily_data)

        return daily_data

    def add_simple_regressors(self, data):
        """Ajoute des régresseurs externes simplifiés pour améliorer les prévisions"""
        # Jours de la semaine (0=Monday, 6=Sunday) - normalisé entre 0 et 1
        data["day_of_week"] = data["DATE"].dt.dayofweek / 6.0

        # Week-end (samedi et dimanche) - binaire
        data["is_weekend"] = data["DATE"].dt.dayofweek.isin([5, 6]).astype(int)

        # Jours fériés du Cameroun - binaire
        data["is_holiday"] = data["DATE"].apply(
            lambda x: 1 if x in self.cameroon_holidays else 0
        )

        # Mois (1-12) - normalisé entre 0 et 1
        data["month"] = (data["DATE"].dt.month - 1) / 11.0

        return data

    def add_regressor(self, name):
        self.extra_regressors.append(name)

    def create_model(
        self,
        daily_data,
        target_col,
        model_name,
        changepoint_prior_scale=0.001,
        seasonality_prior_scale=1.0,
        holidays_prior_scale=1.0,
        seasonality_mode="additive",
    ):
        prophet_data = daily_data[["DATE", target_col]].copy()
        prophet_data.columns = ["ds", "y"]

        # Vérifier et nettoyer les données
        prophet_data = prophet_data.dropna()

        # Vérifier qu'il n'y a pas de valeurs infinies ou négatives
        prophet_data = prophet_data[prophet_data["y"] > 0]
        prophet_data = prophet_data[np.isfinite(prophet_data["y"])]

        if len(prophet_data) == 0:
            raise ValueError(f"Aucune donnée valide pour le modèle {model_name}")

        # Hyperparamètres ultra-conservateurs pour éviter les erreurs Stan
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode=seasonality_mode,
            mcmc_samples=0,  # Pas de MCMC pour éviter les erreurs
            interval_width=0.95,
            changepoint_prior_scale=changepoint_prior_scale,  # Très peu flexible
            seasonality_prior_scale=seasonality_prior_scale,  # Saisonnalité faible
            holidays_prior_scale=holidays_prior_scale,  # Jours fériés faibles
            holidays=self.special_events,
        )

        # Ajouter les régresseurs externes simplifiés
        regressor_cols = ["day_of_week", "is_weekend", "is_holiday", "month"]

        for reg in regressor_cols:
            if reg in daily_data.columns:
                # Vérifier que les régresseurs sont valides
                regressor_values = daily_data[reg].values
                if np.isfinite(regressor_values).all():
                    model.add_regressor(reg)
                    prophet_data[reg] = regressor_values

        # Ajouter les jours fériés du Cameroun
        model.add_country_holidays(country_name="CM")

        try:
            model.fit(prophet_data)
            self.models[model_name] = model
            return model
        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'entraînement du modèle {model_name}: {e}"
            )
            # Essayer sans régresseurs externes
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode="additive",
                mcmc_samples=0,
                interval_width=0.95,
                changepoint_prior_scale=0.001,
                seasonality_prior_scale=1.0,
                holidays_prior_scale=1.0,
                holidays=self.special_events,
            )
            model.add_country_holidays(country_name="CM")
            model.fit(prophet_data)
            self.models[model_name] = model
            return model

    def train_all_models(self, df):
        daily_data = self.prepare_daily_data(df)
        self.create_model(daily_data, "N° PV", "volume")
        self.create_model(daily_data, "PTTC", "revenue")
        self.logger.info("All models trained successfully")
        return daily_data

    def forecast(self, periods=30):
        forecasts = {}
        for name, model in self.models.items():
            future = model.make_future_dataframe(periods=periods)

            # Ajouter les régresseurs externes pour les périodes futures
            future = self._add_future_regressors(future)

            forecast = model.predict(future)
            forecasts[name] = forecast
        return forecasts

    def _add_future_regressors(self, future):
        """Ajoute les régresseurs externes pour les périodes futures"""
        # Jours de la semaine - normalisé
        future["day_of_week"] = future["ds"].dt.dayofweek / 6.0

        # Week-end
        future["is_weekend"] = future["ds"].dt.dayofweek.isin([5, 6]).astype(int)

        # Jours fériés
        future["is_holiday"] = future["ds"].apply(
            lambda x: 1 if x in self.cameroon_holidays else 0
        )

        # Mois - normalisé
        future["month"] = (future["ds"].dt.month - 1) / 11.0

        return future
