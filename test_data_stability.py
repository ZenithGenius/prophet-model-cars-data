#!/usr/bin/env python3
"""
Script de test de stabilité des données avant entraînement
Vérifie la qualité des données et identifie les problèmes potentiels
"""

import pandas as pd
import numpy as np
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_and_check_data():
    """Charge et vérifie la qualité des données"""
    print("🔍 VÉRIFICATION DE LA STABILITÉ DES DONNÉES")
    print("=" * 50)

    # Charger les données
    df = pd.read_csv("dataset/dataset.csv")
    print(f"📊 {len(df)} enregistrements chargés")

    # Convertir DATE
    df["DATE"] = pd.to_datetime(df["DATE"], format="%d/%m/%Y")

    # Vérifications de base
    print("\n📋 VÉRIFICATIONS DE BASE:")
    print(f"  Plage de dates: {df['DATE'].min()} à {df['DATE'].max()}")
    print(f"  Jours uniques: {df['DATE'].nunique()}")
    print(f"  Valeurs manquantes: {df.isnull().sum().sum()}")

    # Vérifier les colonnes numériques
    numeric_cols = ["N° PV", "PTTC", "pht", "TVA", "COUPON"]
    print("\n📊 VÉRIFICATIONS DES COLONNES NUMÉRIQUES:")

    for col in numeric_cols:
        if col in df.columns:
            values = pd.to_numeric(df[col], errors="coerce")
            print(f"\n  {col}:")
            print(f"    Min: {values.min()}")
            print(f"    Max: {values.max()}")
            print(f"    Moyenne: {values.mean():.2f}")
            print(f"    Valeurs négatives: {(values < 0).sum()}")
            print(f"    Valeurs infinies: {np.isinf(values).sum()}")
            print(f"    Valeurs NaN: {values.isna().sum()}")

    return df


def check_daily_aggregation(df):
    """Vérifie l'agrégation quotidienne"""
    print("\n📅 VÉRIFICATION DE L'AGRÉGATION QUOTIDIENNE:")
    print("=" * 50)

    # Agrégation quotidienne
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

    print(f"📊 {len(daily_data)} jours uniques")

    # Vérifier les valeurs
    for col in ["N° PV", "PTTC", "pht", "TVA", "COUPON"]:
        if col in daily_data.columns:
            values = daily_data[col]
            print(f"\n  {col}:")
            print(f"    Min: {values.min()}")
            print(f"    Max: {values.max()}")
            print(f"    Moyenne: {values.mean():.2f}")
            print(f"    Valeurs nulles: {(values == 0).sum()}")
            print(f"    Valeurs négatives: {(values < 0).sum()}")
            print(f"    Valeurs infinies: {np.isinf(values).sum()}")

    return daily_data


def check_regressors(daily_data):
    """Vérifie les régresseurs externes"""
    print("\n🔧 VÉRIFICATION DES RÉGRESSEURS EXTERNES:")
    print("=" * 50)

    import holidays

    # Jours de la semaine
    daily_data["day_of_week"] = daily_data["DATE"].dt.dayofweek / 6.0
    print(
        f"  day_of_week: {daily_data['day_of_week'].min():.3f} à {daily_data['day_of_week'].max():.3f}"
    )

    # Week-end
    daily_data["is_weekend"] = daily_data["DATE"].dt.dayofweek.isin([5, 6]).astype(int)
    print(f"  is_weekend: {daily_data['is_weekend'].value_counts().to_dict()}")

    # Jours fériés
    cameroon_holidays = holidays.Cameroon()
    daily_data["is_holiday"] = daily_data["DATE"].apply(
        lambda x: 1 if x in cameroon_holidays else 0
    )
    print(f"  is_holiday: {daily_data['is_holiday'].value_counts().to_dict()}")

    # Mois
    daily_data["month"] = (daily_data["DATE"].dt.month - 1) / 11.0
    print(f"  month: {daily_data['month'].min():.3f} à {daily_data['month'].max():.3f}")

    return daily_data


def test_prophet_stability(daily_data):
    """Teste la stabilité avec Prophet"""
    print("\n🤖 TEST DE STABILITÉ AVEC PROPHET:")
    print("=" * 50)

    try:
        from prophet import Prophet

        # Test avec le volume
        volume_data = daily_data[["DATE", "N° PV"]].copy()
        volume_data.columns = ["ds", "y"]

        # Nettoyer les données
        volume_data = volume_data.dropna()
        volume_data = volume_data[volume_data["y"] > 0]
        volume_data = volume_data[np.isfinite(volume_data["y"])]

        print(f"📊 Données volume valides: {len(volume_data)} jours")

        if len(volume_data) > 0:
            # Test avec modèle simple
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
            )

            model.fit(volume_data)
            print("✅ Test volume réussi")

            # Test avec régresseurs
            model_with_regressors = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode="additive",
                mcmc_samples=0,
                interval_width=0.95,
                changepoint_prior_scale=0.001,
                seasonality_prior_scale=1.0,
                holidays_prior_scale=1.0,
            )

            # Ajouter un régresseur simple
            model_with_regressors.add_regressor("day_of_week")
            volume_data["day_of_week"] = daily_data["day_of_week"].values[
                : len(volume_data)
            ]

            model_with_regressors.fit(volume_data)
            print("✅ Test avec régresseurs réussi")

        else:
            print("❌ Aucune donnée volume valide")

    except Exception as e:
        print(f"❌ Erreur lors du test Prophet: {e}")


def main():
    """Fonction principale"""
    print("🚀 TEST DE STABILITÉ DES DONNÉES")
    print("=" * 60)

    # Charger et vérifier les données
    df = load_and_check_data()

    # Vérifier l'agrégation quotidienne
    daily_data = check_daily_aggregation(df)

    # Vérifier les régresseurs
    daily_data = check_regressors(daily_data)

    # Tester la stabilité avec Prophet
    test_prophet_stability(daily_data)

    print("\n✅ Test de stabilité terminé")


if __name__ == "__main__":
    main()
