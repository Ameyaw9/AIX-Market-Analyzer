from pathlib import Path

from web3._utils.events import get_event_data
from eth_abi.codec import ABICodec
import pickle

from snet.sdk.mpe.payment_channel import PaymentChannel
from snet.contracts import get_contract_deployment_block


BLOCKS_PER_BATCH = 5000
CHANNELS_DIR = Path.home().joinpath(".snet", "cache", "mpe")


class PaymentChannelProvider(object):
    def __init__(self, w3, mpe_contract):
        self.web3 = w3

        self.mpe_contract = mpe_contract
        self.event_topics = [self.web3.keccak(
            text="ChannelOpen(uint256,uint256,address,address,address,bytes32,uint256,uint256)").hex()]
        self.deployment_block = get_contract_deployment_block(self.web3, "MultiPartyEscrow")
        self.mpe_address = mpe_contract.contract.address
        self.channels_file = CHANNELS_DIR.joinpath(str(self.mpe_address), "channels.pickle")

    def update_cache(self):
        channels = []
        last_read_block = self.deployment_block

        if not self.channels_file.exists():
            print(f"Channels cache is empty. Caching may take some time when first accessing channels.\nCaching in progress...")
            self.channels_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.channels_file, "wb") as f:
                empty_dict = {
                    "last_read_block": last_read_block,
                    "channels": channels
                }
                pickle.dump(empty_dict, f)
        else:
            with open(self.channels_file, "rb") as f:
                load_dict = pickle.load(f)
            last_read_block = load_dict["last_read_block"]
            channels = load_dict["channels"]

        current_block_number = self.web3.eth.block_number

        if last_read_block < current_block_number:
            new_channels = self._get_all_channels_from_blockchain_logs_to_dicts(last_read_block, current_block_number)
            channels = channels + new_channels
            last_read_block = current_block_number

            with open(self.channels_file, "wb") as f:
                dict_to_save = {
                    "last_read_block": last_read_block,
                    "channels": channels
                }
                pickle.dump(dict_to_save, f)

    def _event_data_args_to_dict(self, event_data):
        return {
            "channel_id": event_data["channelId"],
            "sender": event_data["sender"],
            "signer": event_data["signer"],
            "recipient": event_data["recipient"],
            "group_id": event_data["groupId"],
        }

    def _get_all_channels_from_blockchain_logs_to_dicts(self, starting_block_number, to_block_number):
        codec: ABICodec = self.web3.codec

        logs = []
        from_block = starting_block_number
        while from_block <= to_block_number:
            to_block = min(from_block + BLOCKS_PER_BATCH, to_block_number)
            logs = logs + self.web3.eth.get_logs({"fromBlock": from_block,
                                                  "toBlock": to_block,
                                                  "address": self.mpe_address,
                                                  "topics": self.event_topics})
            from_block = to_block + 1

        event_abi = self.mpe_contract.contract._find_matching_event_abi(event_name="ChannelOpen")

        event_data_list = [get_event_data(codec, event_abi, l)["args"] for l in logs]
        channels_opened = list(map(self._event_data_args_to_dict, event_data_list))

        return channels_opened

    def _get_channels_from_cache(self):
        self.update_cache()
        with open(self.channels_file, "rb") as f:
            load_dict = pickle.load(f)
        return load_dict["channels"]

    def get_past_open_channels(self, account, payment_address, group_id, payment_channel_state_service_client):

        dict_channels = self._get_channels_from_cache()

        channels_opened = list(filter(lambda channel: (channel["sender"] == account.address
                                                       or channel["signer"] == account.signer_address)
                                                      and channel["recipient"] == payment_address
                                                      and channel["group_id"] == group_id,
                                      dict_channels))

        return list(map(lambda channel: PaymentChannel(channel["channel_id"],
                                                       self.web3,
                                                       account,
                                                       payment_channel_state_service_client,
                                                       self.mpe_contract),
                        channels_opened))

    def open_channel(self, account, amount, expiration, payment_address, group_id, payment_channel_state_service_client):
        receipt = self.mpe_contract.open_channel(account, payment_address, group_id, amount, expiration)
        return self._get_newly_opened_channel(account, payment_address, group_id, receipt, payment_channel_state_service_client)

    def deposit_and_open_channel(self, account, amount, expiration, payment_address, group_id, payment_channel_state_service_client):
        receipt = self.mpe_contract.deposit_and_open_channel(account, payment_address, group_id, amount, expiration)
        return self._get_newly_opened_channel(account, payment_address, group_id, receipt, payment_channel_state_service_client)

    def _get_newly_opened_channel(self, account, payment_address, group_id, receipt, payment_channel_state_service_client):
        open_channels = self.get_past_open_channels(account, payment_address, group_id, payment_channel_state_service_client)
        if not open_channels:
            raise Exception(f"Error while opening channel, please check transaction {receipt.transactionHash.hex()} ")
        return open_channels[-1]

