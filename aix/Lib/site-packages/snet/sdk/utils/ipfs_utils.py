""" Utilities related to ipfs """
import base58
import ipfshttpclient
import multihash


def get_from_ipfs_and_checkhash(ipfs_client, ipfs_hash_base58, validate=True):
    """
    Get file from IPFS. If validate is True, verify the integrity of the file using its hash.
    """

    data = ipfs_client.cat(ipfs_hash_base58)

    if validate:
        block_data = ipfs_client.block.get(ipfs_hash_base58)

        # print(f"IPFS hash (Base58): {ipfs_hash_base58}")
        # print(f"Block data length: {len(block_data)}")

        # Decode Base58 bash to multihash
        try:
            mh = multihash.decode(ipfs_hash_base58.encode('ascii'), "base58")
        except Exception as e:
            raise ValueError(f"Invalid multihash for IPFS hash: {ipfs_hash_base58}. Error: {str(e)}") from e

        if not mh.verify(block_data):  # Correctly using mh instance for verification
            raise Exception("IPFS hash mismatch with data")

    return data

def get_ipfs_client(config):
    ipfs_endpoint = config.get_ipfs_endpoint()
    return ipfshttpclient.connect(ipfs_endpoint)

