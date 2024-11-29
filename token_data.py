import os
import pandas as pd
import json
from typing import List, Dict, Optional

class MarketDataCollector:
    def __init__(self, tokens: List[str], csv_directory: str):
        """
        Initialize data collector with tokens and directory of CSV files
        
        :param tokens: List of cryptocurrency tokens
        :param csv_directory: Directory containing token-specific CSV files
        """
        self.tokens = [f"{token}-USD" for token in tokens]
        self.csv_directory = csv_directory
        self.data = {}
    
    def load_from_csv(self) -> Dict:
        """
        Load market data from individual token CSV files
        
        :return: Dictionary of token market data
        """
        metrics = {}
        
        for token in self.tokens:
            # Remove '-USD' for filename
            token_name = token.split('-')[0]
            
            # Construct potential CSV filenames
            possible_filenames = [
                f"{token_name}.csv",
                f"{token_name}_data.csv",
                f"{token_name}_token.csv"
            ]
            
            # Find the correct file
            csv_path = None
            for filename in possible_filenames:
                potential_path = os.path.join(self.csv_directory, filename)
                if os.path.exists(potential_path):
                    csv_path = potential_path
                    break
            
            if not csv_path:
                print(f"Warning: No CSV file found for token {token_name}")
                continue
            
            # Read the CSV file
            try:
                df = pd.read_csv(csv_path)
                
                metrics[token] = {
                    'start_dates': df['Start'].tolist() if 'Start' in df.columns else [],
                    'end_dates': df['End'].tolist() if 'End' in df.columns else [],
                    'open_prices': df['Open'].tolist() if 'Open' in df.columns else [],
                    'high_prices': df['High'].tolist() if 'High' in df.columns else [],
                    'low_prices': df['Low'].tolist() if 'Low' in df.columns else [],
                    'close_prices': df['Close'].tolist() if 'Close' in df.columns else [],
                    'volumes': df['Volume'].tolist() if 'Volume' in df.columns else [],
                    'market_caps': df['Market Cap'].tolist() if 'Market Cap' in df.columns else [],
                    'social_sentiment': self.fetch_social_sentiment(token_name)
                }
                
                # Store full dataframe
                self.data[token] = df
            
            except Exception as e:
                print(f"Error loading CSV for {token_name}: {e}")
        
        return metrics
    
    def fetch_social_sentiment(self, token: str):
        """
        Fetch social media sentiment (mock implementation)
        
        :param token: Token to analyze
        :return: Sentiment score dictionary
        """
        sentiments = {
            'positive': 0.6,
            'neutral': 0.3,
            'negative': 0.1
        }
        return sentiments
    
    def get_token_metrics(self) -> Dict:
        """
        Compile key metrics for each token
        
        :return: Dictionary of token metrics
        """
        if not self.data:
            self.load_from_csv()
        
        return self.data
    
    def save_data(self, filename: str = 'market_data.json'):
        """
        Save collected data to a JSON file
        
        :param filename: Output filename
        """
        with open(filename, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.data.items()}, 
                f, 
                indent=4
            )

def main():
    # Tokens you want to analyze
    tokens = ['FET', 'OCEAN', 'NEAR', 'AGIX', 'NMR', 'RNDR']
    
    # Path to directory containing individual token CSVs
    csv_directory = r'\Users\PC\AIX_Market_Analyzer\Tokens'
    
    # Initialize collector
    collector = MarketDataCollector(tokens, csv_directory)
    
    # Load market metrics
    market_metrics = collector.load_from_csv()
    
    # Print or process the metrics
    for token, metrics in market_metrics.items():
        print(f"Loaded data for {token}")
        print(f"Close prices: {metrics['close_prices'][:5]}...")  # Print first 5 close prices
        print(f"Total data points: {len(metrics['close_prices'])}\n")

if __name__ == "__main__":
    main()