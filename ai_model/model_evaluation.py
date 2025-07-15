import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging

class ModelEvaluator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_metrics(self, actual, predicted):
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}

    def evaluate_models(self, daily_data, forecasts):
        results = {}
        for model_name, forecast in forecasts.items():
            if model_name == 'volume':
                actual = daily_data['N° PV'].values
                predicted = forecast['yhat'].values[:len(actual)]
            elif model_name == 'revenue':
                actual = daily_data['PTTC'].values
                predicted = forecast['yhat'].values[:len(actual)]
            else:
                continue
            metrics = self.calculate_metrics(actual, predicted)
            results[model_name] = metrics
            self.logger.info(f"{model_name} model metrics: {metrics}")
        return results
