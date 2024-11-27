from snet.sdk import SnetSDK
import os
import json

class SnetConfig:
    """Custom configuration class that implements required methods"""
    def __init__(self, config_dict):
        self._config = config_dict

    def get_ipfs_endpoint(self):
        return self._config['ipfs_endpoint']

    def get_eth_rpc_endpoint(self):
        return self._config['eth_rpc_endpoint']

    def get_private_key(self):
        return self._config['private_key']

    def get(self, key, default=None):
        return self._config.get(key, default)

    # Make the class subscriptable
    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value

# Configuration dictionary
config_dict = {
    "private_key": os.getenv("SNET_PRIVATE_KEY", "private key here"),
    "eth_rpc_endpoint": "https://mainnet.infura.io/v3/39b6ef5417ab4b9195aa5a34c2a4a134",
    "ipfs_endpoint": "/ip4/ipfs.singularitynet.io/tcp/80",  # Updated IPFS endpoint format
    "ipfs_timeout": 10,
    "org_id": "26072b8b6a0e448180f8c0e702ab6d2f", 
    "service_id": "Exampleservice", 
    "group_name": "default_group",
    "free_call_auth_token_bin": "f2548d27ffd319b9c05918eeac15ebab934e5cfcd68e1ec3db2b92765",
    "free_call_token_expiry_block": 172800,
    "email": "emmanuel97ameyaw@gmail.com"
}

class SnetAIClient:
    def __init__(self):
        try:
            # Create config object with required methods
            self.config = SnetConfig(config_dict)
            # Initialize SDK with config object
            self.sdk = SnetSDK(self.config)
            print("SDK initialized successfully")
        except Exception as e:
            print(f"Error initializing SDK: {str(e)}")
            raise

    def test_connection(self):
        try:
            # Create service client
            service_client = self.sdk.create_service_client(
                org_id=self.config['org_id'],
                service_id=self.config['service_id'],
                group_name=self.config['group_name']
            )
            print("Service client created successfully")
            return service_client
            
        except Exception as e:
            print(f"Error in test_connection: {str(e)}")
            raise

def main():
    try:
        print("\nInitializing SingularityNET client...")
        client = SnetAIClient()
        print("\nTesting connection...")
        client.test_connection()
        print("\nConnection test completed successfully")
        
    except Exception as e:
        print(f"\nError in main: {str(e)}")
        print("\nDebug information:")
        print(f"SNET_PRIVATE_KEY set: {'Yes' if os.getenv('SNET_PRIVATE_KEY') else 'No'}")
        print(f"Config used: {json.dumps(config_dict, indent=2, default=str)}")

if __name__ == "__main__":
    main()