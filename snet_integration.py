from config import snet_sdk
import pandas as pd

class AITokenService:
    def __init__(self):
        # Create service client for the example service
        self.service_client = snet_sdk.create_service_client(
            org_id="26072b8b6a0e448180f8c0e702ab6d2f",
            service_id="Exampleservice",
            group_name="default_group"
        )

    def test_connection(self):
        """Test the SDK connection with a simple calculation"""
        try:
            result = self.service_client.call_rpc(
                "add",
                "Numbers",
                a=10,
                b=5
            )
            print(f"Connection test successful. 10 + 5 = {result}")
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    def process_token_data(self, token_file):
        """Process token data using the service"""
        try:
            # Load token data
            df = pd.read_csv(f'Tokens/{token_file}')
            
            # Get latest price and volume
            latest_price = float(df['Close'].iloc[-1])
            latest_volume = float(df['Volume'].iloc[-1])
            
            # Use the service to process data
            result = self.service_client.call_rpc(
                "mul",  # Example operation
                "Numbers",
                a=latest_price,
                b=latest_volume
            )
            
            return {
                "token": token_file,
                "calculation_result": result,
                "latest_price": latest_price,
                "latest_volume": latest_volume
            }
            
        except Exception as e:
            print(f"Error processing token data: {str(e)}")
            raise

def main():
    # Initialize the service
    ai_service = AITokenService()
    
    # Test the connection
    if ai_service.test_connection():
        print("SDK connection successful!")
        
        # Process each token
        tokens = ['AGIX.csv', 'FET.csv', 'NEAR.csv', 'NMR.csv', 'OCEAN.csv', 'RNDR.csv']
        
        for token in tokens:
            try:
                result = ai_service.process_token_data(token)
                print(f"\nProcessed {token}:")
                print(f"Latest Price: {result['latest_price']}")
                print(f"Latest Volume: {result['latest_volume']}")
                print(f"Calculation Result: {result['calculation_result']}")
            except Exception as e:
                print(f"Error processing {token}: {str(e)}")

if __name__ == "__main__":
    main()