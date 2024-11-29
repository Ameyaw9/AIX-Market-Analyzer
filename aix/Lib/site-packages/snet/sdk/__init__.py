import importlib
import os
from pathlib import Path
import sys
from typing import Any, NewType
import warnings

import google.protobuf.internal.api_implementation

from snet.sdk.mpe.payment_channel_provider import PaymentChannelProvider

with warnings.catch_warnings():
    # Suppress the eth-typing package`s warnings related to some new networks
    warnings.filterwarnings("ignore", "Network .* does not have a valid ChainId. eth-typing should be "
                                      "updated with the latest networks.", UserWarning)
    from snet.sdk.storage_provider.storage_provider import StorageProvider

from snet.sdk.payment_strategies.default_payment_strategy import DefaultPaymentStrategy
from snet.sdk.client_lib_generator import ClientLibGenerator
from snet.sdk.config import Config
from snet.sdk.utils.utils import bytes32_to_str, type_converter

google.protobuf.internal.api_implementation.Type = lambda: 'python'

from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
_sym_db.RegisterMessage = lambda x: None

import web3

from snet.sdk.service_client import ServiceClient
from snet.sdk.account import Account
from snet.sdk.mpe.mpe_contract import MPEContract

from snet.contracts import get_contract_object

from snet.sdk.storage_provider.service_metadata import mpe_service_metadata_from_json
from snet.sdk.utils.ipfs_utils import get_from_ipfs_and_checkhash
from snet.sdk.utils.utils import find_file_by_keyword

ModuleName = NewType('ModuleName', str)
ServiceStub = NewType('ServiceStub', Any)


class SnetSDK:
    """Base Snet SDK"""

    def __init__(self, sdk_config: Config, metadata_provider=None):
        self._sdk_config = sdk_config
        self._metadata_provider = metadata_provider

        # Instantiate Ethereum client
        eth_rpc_endpoint = self._sdk_config["eth_rpc_endpoint"]
        eth_rpc_request_kwargs = self._sdk_config.get("eth_rpc_request_kwargs")

        provider = web3.HTTPProvider(endpoint_uri=eth_rpc_endpoint, request_kwargs=eth_rpc_request_kwargs)

        self.web3 = web3.Web3(provider)

        # Get MPE contract address from config if specified; mostly for local testing
        _mpe_contract_address = self._sdk_config.get("mpe_contract_address", None)
        if _mpe_contract_address is None:
            self.mpe_contract = MPEContract(self.web3)
        else:
            self.mpe_contract = MPEContract(self.web3, _mpe_contract_address)

        # Get Registry contract address from config if specified; mostly for local testing
        _registry_contract_address = self._sdk_config.get("registry_contract_address", None)
        if _registry_contract_address is None:
            self.registry_contract = get_contract_object(self.web3, "Registry")
        else:
            self.registry_contract = get_contract_object(self.web3, "Registry", _registry_contract_address)

        if self._metadata_provider is None:
            self._metadata_provider = StorageProvider(self._sdk_config, self.registry_contract)

        self.account = Account(self.web3, sdk_config, self.mpe_contract)
        self.payment_channel_provider = PaymentChannelProvider(self.web3, self.mpe_contract)

    def create_service_client(self, org_id: str, service_id: str, group_name=None,
                              payment_channel_management_strategy=None,
                              free_call_auth_token_bin=None,
                              free_call_token_expiry_block=None,
                              email=None,
                              options=None,
                              concurrent_calls=1):

        # Create and instance of the Config object, so we can create an instance of ClientLibGenerator
        lib_generator = ClientLibGenerator(self._metadata_provider, org_id, service_id)

        # Download the proto file and generate stubs if needed
        force_update = self._sdk_config.get('force_update', False)
        if force_update:
            lib_generator.generate_client_library()
        else:
            path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
            pb_2_file_name = find_file_by_keyword(path_to_pb_files, keyword="pb2.py")
            pb_2_grpc_file_name = find_file_by_keyword(path_to_pb_files, keyword="pb2_grpc.py")
            if not pb_2_file_name or not pb_2_grpc_file_name:
                lib_generator.generate_client_library()
        
        if payment_channel_management_strategy is None:
            payment_channel_management_strategy = DefaultPaymentStrategy(concurrent_calls)

        if options is None:
            options = dict()
        options['free_call_auth_token-bin'] = bytes.fromhex(free_call_auth_token_bin) if\
            free_call_token_expiry_block else ""
        options['free-call-token-expiry-block'] = free_call_token_expiry_block if\
            free_call_token_expiry_block else 0
        options['email'] = email if email else ""
        options['concurrency'] = self._sdk_config.get("concurrency", True)

        service_metadata = self._metadata_provider.enhance_service_metadata(org_id, service_id)
        group = self._get_service_group_details(service_metadata, group_name)
        strategy = payment_channel_management_strategy
        
        service_stub = self.get_service_stub(org_id, service_id)
        
        pb2_module = self.get_module_by_keyword(org_id, service_id, keyword="pb2.py")
        
        _service_client = ServiceClient(org_id, service_id, service_metadata, group, service_stub, strategy,
                                       options, self.mpe_contract, self.account, self.web3, pb2_module, self.payment_channel_provider)
        return _service_client

    def get_service_stub(self, org_id: str, service_id: str) -> ServiceStub:
        path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
        module_name = self.get_module_by_keyword(org_id, service_id, keyword="pb2_grpc.py")
        package_path = os.path.dirname(path_to_pb_files)
        sys.path.append(package_path)
        try:
            grpc_file = importlib.import_module(module_name)
            properties_and_methods_of_grpc_file = dir(grpc_file)
            class_stub = [elem for elem in properties_and_methods_of_grpc_file if 'Stub' in elem][0]
            service_stub = getattr(grpc_file, class_stub)
            return ServiceStub(service_stub)
        except Exception as e:
            raise Exception(f"Error importing module: {e}")

    def get_path_to_pb_files(self, org_id: str, service_id: str) -> str:
        client_libraries_base_dir_path = Path("~").expanduser().joinpath(".snet")
        path_to_pb_files = f"{client_libraries_base_dir_path}/{org_id}/{service_id}/python/"
        return path_to_pb_files
    
    def get_module_by_keyword(self, org_id: str, service_id: str, keyword: str) -> ModuleName:
        path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
        file_name = find_file_by_keyword(path_to_pb_files, keyword)
        module_name = os.path.splitext(file_name)[0]
        return ModuleName(module_name)

    def get_service_metadata(self, org_id, service_id):
        return self._metadata_provider.fetch_service_metadata(org_id, service_id)

    def _get_first_group(self, service_metadata):
        return service_metadata['groups'][0]

    def _get_group_by_group_name(self, service_metadata, group_name):
        for group in service_metadata['groups']:
            if group['group_name'] == group_name:
                return group
        return {}

    def _get_service_group_details(self, service_metadata, group_name):
        if len(service_metadata['groups']) == 0:
            raise Exception("No Groups found for given service, Please add group to the service")

        if group_name is None:
            return self._get_first_group(service_metadata)

        return self._get_group_by_group_name(service_metadata, group_name)

    def get_organization_list(self) -> list:
        org_list = self.registry_contract.functions.listOrganizations().call()
        organization_list = []
        for idx, org_id in enumerate(org_list):
            organization_list.append(bytes32_to_str(org_id))
        return organization_list

    def get_services_list(self, org_id: str) -> list:
        found, org_service_list = self.registry_contract.functions.listServicesForOrganization(
            type_converter("bytes32")(org_id)
        ).call()
        if not found:
            raise Exception(f"Organization with id={org_id} doesn't exist!")
        org_service_list = list(map(bytes32_to_str, org_service_list))
        return org_service_list

