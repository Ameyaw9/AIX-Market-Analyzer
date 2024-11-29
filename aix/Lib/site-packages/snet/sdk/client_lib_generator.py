import os
from pathlib import Path, PurePath

from snet.sdk import StorageProvider
from snet.sdk.utils import ipfs_utils
from snet.sdk.utils.utils import compile_proto, type_converter


class ClientLibGenerator:

    def __init__(self, metadata_provider, org_id, service_id):
        self._metadata_provider = metadata_provider
        self.org_id = org_id
        self.service_id = service_id
        self.language = "python"
        self.protodir = Path("~").expanduser().joinpath(".snet")

    def generate_client_library(self):

        if os.path.isabs(self.protodir):
            client_libraries_base_dir_path = PurePath(self.protodir)
        else:
            cur_dir_path = PurePath(os.getcwd())
            client_libraries_base_dir_path = cur_dir_path.joinpath(self.protodir)

        os.makedirs(client_libraries_base_dir_path, exist_ok=True)

        # Create service client libraries path
        library_language = self.language
        library_org_id = self.org_id
        library_service_id = self.service_id

        library_dir_path = client_libraries_base_dir_path.joinpath(library_org_id,
                                                                   library_service_id,
                                                                   library_language)

        try:
            metadata = self._metadata_provider.fetch_service_metadata(self.org_id, self.service_id)
            service_api_source = metadata.get("service_api_source") or metadata.get("model_ipfs_hash")

            # Receive proto files
            self._metadata_provider.fetch_and_extract_proto(service_api_source, library_dir_path)

            # Compile proto files
            compile_proto(Path(library_dir_path), library_dir_path, target_language=self.language)

            print(f'client libraries for service with id "{library_service_id}" in org with id "{library_org_id}" '
                  f'generated at {library_dir_path}')
        except Exception as e:
            print(e)
