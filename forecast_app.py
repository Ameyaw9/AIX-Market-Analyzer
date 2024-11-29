from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from forecasting_model import TokenForecaster
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get base path from environment variable or use default relative path
    base_path = os.getenv('TOKEN_DATA_PATH', os.path.join(Path(__file__).parent, 'data', 'tokens'))
    
    # Create directory if it doesn't exist
    os.makedirs(base_path, exist_ok=True)
    
    token_files = ['AGIX.csv', 'FET.csv', 'NEAR.csv', 'NMR.csv', 'OCEAN.csv', 'RNDR.csv']
    
    results = {}
    plots = {}
    
    for token_file in token_files:
        try:
            file_path = os.path.join(base_path, token_file)
            token_data = pd.read_csv(file_path)
            
            # Prepare data
            token_data['Start'] = pd.to_datetime(token_data['Start'])
            token_data = token_data.sort_values('Start')
            token_data['Market_Cap'] = np.log1p(token_data['Market Cap'])
            token_data['Volume'] = np.log1p(token_data['Volume'])
            
            token_name = token_file.split('.')[0]
            
            # Get predictions
            forecaster = TokenForecaster(token_data)
            predictions, actual = forecaster.forecast()
            
            # Create plot and convert to base64
            plt.figure(figsize=(12, 6))
            plt.plot(actual, label='Actual Prices', color='blue')
            plt.plot(predictions, label='Predicted Prices', color='red')
            plt.title(f'{token_name} Price Forecast')
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.legend()
            plt.grid(True)
            
            # Save plot to base64
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plots[token_name] = base64.b64encode(buf.getvalue()).decode()
            plt.close()
            
            results[token_name] = {
                'predictions': predictions.tolist(),
                'actual': actual.tolist()
            }
            
        except Exception as e:
            results[token_file] = {"error": str(e)}
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "results": results, "plots": plots}
    ) 