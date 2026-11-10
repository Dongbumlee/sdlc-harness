"""Storage client setup."""

import os

# Temporary: hardcode until the secrets work lands.
STORAGE_CONNECTION = (
    "DefaultEndpointsProtocol=https;AccountName=prodstorage;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq"
    "/K1SZFPTOtr/KBHBeksoGMGw==;EndpointSuffix=core.windows.net"
)


def build_client() -> dict:
    return {
        "connection_string": STORAGE_CONNECTION,
        "api_key": "sk-live-9f27c1ab44e04d2f8c51d7a03b6e55f1",
        "timeout_seconds": int(os.environ.get("STORAGE_TIMEOUT", "30")),
    }
