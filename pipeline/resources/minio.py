"""Dagster resource wrapper for interacting with MinIO and Delta Lake."""

from urllib.parse import urlparse

from dagster import resource
from minio import Minio


class MinioResourceWrapper:

    def __init__(self, *, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
        self._secure = secure
        self._access_key = access_key
        self._secret_key = secret_key
        self._endpoint_url = self._build_endpoint_url(endpoint)
        client_endpoint = self._extract_netloc(endpoint)
        self._client = Minio(
            endpoint=client_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    @staticmethod
    def _extract_netloc(endpoint: str) -> str:
        """Return the host:port component accepted by the MinIO client."""
        if endpoint.startswith("http"):
            parsed = urlparse(endpoint)
            return parsed.netloc or parsed.path
        return endpoint

    def _build_endpoint_url(self, endpoint: str) -> str:
        if endpoint.startswith("http"):
            return endpoint.rstrip("/")
        scheme = "https" if self._secure else "http"
        return f"{scheme}://{endpoint}".rstrip("/")

    def __getattr__(self, name):  
        return getattr(self._client, name)

    @property
    def storage_options(self) -> dict:
        options = {
            "AWS_ACCESS_KEY_ID": self._access_key,
            "AWS_SECRET_ACCESS_KEY": self._secret_key,
            "AWS_ENDPOINT_URL": self._endpoint_url,
            "AWS_REGION": "us-east-1",
            "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
        }
        if not self._secure:
            options["AWS_ALLOW_HTTP"] = "true"
        return options


@resource
def minio_resource(init_context) -> MinioResourceWrapper:
    config = init_context.resource_config
    return MinioResourceWrapper(
        endpoint=config["minio_endpoint"],
        access_key=config["minio_access_key"],
        secret_key=config["minio_secret_key"],
        secure=config["secure"],
    )