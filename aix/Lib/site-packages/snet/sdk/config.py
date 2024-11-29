

class Config:
    def __init__(self,
                 private_key,
                 eth_rpc_endpoint,
                 wallet_index=0,
                 ipfs_endpoint=None,
                 concurrency=True,
                 force_update=False,
                 mpe_contract_address=None,
                 token_contract_address=None,
                 registry_contract_address=None,
                 signer_private_key=None):
        self.__config = {
            "private_key": private_key,
            "eth_rpc_endpoint": eth_rpc_endpoint,
            "wallet_index": wallet_index,
            "ipfs_endpoint": ipfs_endpoint if ipfs_endpoint else "/dns/ipfs.singularitynet.io/tcp/80/",
            "concurrency": concurrency,
            "force_update": force_update,
            "mpe_contract_address": mpe_contract_address,
            "token_contract_address": token_contract_address,
            "registry_contract_address": registry_contract_address,
            "signer_private_key": signer_private_key,
            "lighthouse_token": " "
        }

    def __getitem__(self, key):
        return self.__config[key]

    def get(self, key, default=None):
        return self.__config.get(key, default)

    def get_ipfs_endpoint(self):
        return self["ipfs_endpoint"]

