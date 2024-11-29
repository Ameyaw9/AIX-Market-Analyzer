from snet import sdk
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

config = sdk.config.Config(
    private_key=os.getenv("SNET_PRIVATE_KEY"),
    eth_rpc_endpoint=f"https://sepolia.infura.io/v3/{os.getenv('INFURA_KEY')}",  
    concurrency=False,
    force_update=False
)

snet_sdk = sdk.SnetSDK(config)