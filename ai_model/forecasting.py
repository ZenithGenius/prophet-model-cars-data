from ai_model.prophet_models import PVProphetModel

def run_forecasting(df, forecast_periods=30, output_prefix="forecast"):
    model = PVProphetModel()
    daily_data = model.train_all_models(df)
    forecasts = model.forecast(periods=forecast_periods)
    # Sauvegarder les prévisions dans des fichiers CSV
    for name, forecast in forecasts.items():
        forecast.to_csv(f"{output_prefix}_{name}.csv", index=False)
    return forecasts, daily_data
