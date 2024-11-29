import numpy as np
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt

class TokenForecaster:
    def __init__(self, token_data: pd.DataFrame):
        """
        Initialize forecaster with enhanced token data
        
        :param token_data: DataFrame with historical price and additional features
        """
        self.data = token_data
        self.model = None
        self.scaler = MinMaxScaler()
        
    def prepare_lstm_data(self, look_back: int = 60):
       
     
        # Use multiple features: Close, Volume, Market Cap
        features = ['Close', 'Volume', 'Market_Cap']
        scaled_data = self.scaler.fit_transform(self.data[features])
        
        X, y = [], []
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i-look_back:i])
            y.append(scaled_data[i, 0])  # Still predicting Close price
            
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, input_shape):
        """
        Enhanced LSTM model with multiple features
        
        :param input_shape: Shape of input data
        """
        self.model = Sequential([
            LSTM(100, activation='relu', input_shape=(input_shape[1], input_shape[2]), return_sequences=True),
            LSTM(50, activation='relu'),
            Dense(25),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')
    
    def train_model(self, X_train, y_train, epochs=50, batch_size=32):
        """
        Train the LSTM model
        
        :param X_train: Training input data
        :param y_train: Training target data
        :param epochs: Number of training epochs
        :param batch_size: Batch size for training
        """
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
    
    def forecast(self, look_back: int = 60):
        """
        Generate price forecasts
        
        :param look_back: Number of previous time steps to use
        :return: Forecasted prices and actual test data
        """
        X, y = self.prepare_lstm_data(look_back)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.build_lstm_model(X_train.shape)
        self.train_model(X_train, y_train)
        
        # Predict
        predictions = self.model.predict(X_test)
        
        # Inverse transform predictions to get actual price values
        pred_matrix = np.zeros((len(predictions), 3))  # 3 features
        pred_matrix[:, 0] = predictions.flatten()
        
        predictions = self.scaler.inverse_transform(pred_matrix)[:, 0]
        
        # Inverse transform actual values
        actual_matrix = np.zeros((len(y_test), 3))
        actual_matrix[:, 0] = y_test
        actual_values = self.scaler.inverse_transform(actual_matrix)[:, 0]
        
        return predictions, actual_values
    
    def plot_forecast(self, predictions, actual, token_name=""):
        """
        Plot forecasted vs actual prices
        
        :param predictions: Predicted prices
        :param actual: Actual prices
        :param token_name: Name of the token being analyzed
        """
        plt.figure(figsize=(12, 6))
        plt.plot(actual, label='Actual Prices', color='blue')
        plt.plot(predictions, label='Predicted Prices', color='red')
        plt.title(f'{token_name} Price Forecast')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()

    def add_technical_indicators(self):
        """
        Add technical indicators to the dataset
        """
        # Example implementation - can be expanded
        # Calculate moving averages
        self.data['MA7'] = self.data['Close'].rolling(window=7).mean()
        self.data['MA21'] = self.data['Close'].rolling(window=21).mean()
        
        # Fill NaN values
        self.data.fillna(method='bfill', inplace=True)

def main():
    # List of token files
    token_files = ['AGIX.csv', 'FET.csv', 'NEAR.csv', 'NMR.csv', 'OCEAN.csv', 'RNDR.csv']
    base_path = r'C:\Users\PC\AIX_Market_Analyzer\Tokens'
    
    results = {}
    
    for token_file in token_files:
        try:
            # Load and prepare data for each token
            file_path = os.path.join(base_path, token_file)
            token_data = pd.read_csv(file_path)
            
            # Convert to datetime and sort
            token_data['Start'] = pd.to_datetime(token_data['Start'])
            token_data = token_data.sort_values('Start')
            
            # Normalize Market Cap and Volume using log transformation
            token_data['Market_Cap'] = np.log1p(token_data['Market Cap'])
            token_data['Volume'] = np.log1p(token_data['Volume'])
            
            token_name = token_file.split('.')[0]
            print(f"\nAnalyzing {token_name} token...")
            
            forecaster = TokenForecaster(token_data)
            predictions, actual = forecaster.forecast()
            forecaster.plot_forecast(predictions, actual, token_name)
            
            # Store results for potential cross-token analysis
            results[token_name] = {
                'predictions': predictions,
                'actual': actual
            }
            
        except Exception as e:
            print(f"Error processing {token_file}: {str(e)}")
    
    return results

if __name__ == "__main__":
    results = main()