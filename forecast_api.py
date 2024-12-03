from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from typing import List, Dict
from pydantic import BaseModel
from forecasting_model import TokenForecaster
import io

app = FastAPI(title="Token Price Forecaster API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aix-market-analyzer.vercel.app/"], # Frontend linked
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastResult(BaseModel):
    token_name: str
    predictions: List[float]
    actual_values: List[float]

@app.post("/forecast/single", response_model=ForecastResult)
async def forecast_single_token(file: UploadFile = File(...)):
    """
    Process a single token's CSV file and return predictions
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Prepare data
        df['Start'] = pd.to_datetime(df['Start'])
        df = df.sort_values('Start')
        df['Market_Cap'] = np.log1p(df['Market Cap'])
        df['Volume'] = np.log1p(df['Volume'])
        
        # Generate forecast
        forecaster = TokenForecaster(df)
        predictions, actual = forecaster.forecast()
        
        return {
            "token_name": file.filename.split('.')[0],
            "predictions": predictions.tolist(),
            "actual_values": actual.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/forecast/batch")
async def forecast_batch_tokens(files: List[UploadFile] = File(...)):
    """
    Process multiple token CSV files and return predictions
    """
    results = {}
    for file in files:
        try:
            contents = await file.read()
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            
            # Prepare data
            df['Start'] = pd.to_datetime(df['Start'])
            df = df.sort_values('Start')
            df['Market_Cap'] = np.log1p(df['Market Cap'])
            df['Volume'] = np.log1p(df['Volume'])
            
            token_name = file.filename.split('.')[0]
            forecaster = TokenForecaster(df)
            predictions, actual = forecaster.forecast()
            
            results[token_name] = {
                "predictions": predictions.tolist(),
                "actual_values": actual.tolist()
            }
            
        except Exception as e:
            results[file.filename] = {"error": str(e)}
    
    return JSONResponse(content=results)

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
