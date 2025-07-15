from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
import joblib
from ai_model.prophet_models import PVProphetModel

app = FastAPI(title="PV-Autofill Prophet API")

MODEL_PATH = "api/prophet_model.joblib"
DATA_PATH = "dataset/dataset.csv"

# Stockage du modèle en mémoire
model: Optional[PVProphetModel] = None
is_trained = False

class PredictRequest(BaseModel):
    dates: List[str]  # format 'YYYY-MM-DD'

@app.get("/status")
def status():
    return {"trained": os.path.exists(MODEL_PATH)}

@app.post("/train")
def train():
    global model, is_trained
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Dataset non trouvé.")
    df = pd.read_csv(DATA_PATH)
    model = PVProphetModel()
    model.train_all_models(df)
    joblib.dump(model, MODEL_PATH)
    is_trained = True
    return {"message": "Modèle entraîné et sauvegardé."}

@app.post("/predict")
def predict(req: PredictRequest):
    global model, is_trained
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail="Modèle non entraîné. Lancez /train d'abord.")
    if model is None:
        model = joblib.load(MODEL_PATH)
        is_trained = True
    # Préparer les dates futures
    future = pd.DataFrame({"ds": pd.to_datetime(req.dates)})
    future = model._add_future_regressors(future)
    # Prédire volume et revenu
    results = {}
    for name in ["volume", "revenue"]:
        if name in model.models:
            forecast = model.models[name].predict(future)
            results[name] = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_dict(orient="records")
    return {"predictions": results}