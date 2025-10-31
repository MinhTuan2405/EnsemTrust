from minio import Minio
from dagster import resource

@resource
def minio_resource (init_config):
    client = Minio (
        endpoint=init_config.resource_config['minio_endpoint'],
        access_key=init_config.resource_config['minio_access_key'],
        secret_key=init_config.resource_config['minio_secret_key'],
        secure=init_config.resource_config["secure"],
    )

    return client