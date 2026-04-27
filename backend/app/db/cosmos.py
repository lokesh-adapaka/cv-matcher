import logging
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError
from app.config import get_settings

logger = logging.getLogger(__name__)

_client = None
_database = None
_containers: dict = {}

CONTAINERS_CONFIG = {
    "cvs": "/id",
    "jobs": "/id",
    "matches": "/cv_id",
}


def get_cosmos_client() -> CosmosClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
    return _client


def get_database():
    global _database
    if _database is None:
        settings = get_settings()
        client = get_cosmos_client()
        _database = client.create_database_if_not_exists(id=settings.cosmos_database)
    return _database


def get_container(name: str):
    if name not in _containers:
        db = get_database()
        partition_key = CONTAINERS_CONFIG.get(name, "/id")
        try:
            _containers[name] = db.create_container_if_not_exists(
                id=name,
                partition_key=PartitionKey(path=partition_key),
            )
        except CosmosResourceExistsError:
            _containers[name] = db.get_container_client(name)
    return _containers[name]


def upsert_item(container_name: str, item: dict) -> dict:
    container = get_container(container_name)
    return container.upsert_item(body=item)


def read_item(container_name: str, item_id: str, partition_key: str) -> dict | None:
    container = get_container(container_name)
    try:
        return container.read_item(item=item_id, partition_key=partition_key)
    except Exception:
        return None


def query_items(container_name: str, query: str, parameters: list | None = None) -> list:
    container = get_container(container_name)
    return list(
        container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True,
        )
    )


def delete_item(container_name: str, item_id: str, partition_key: str) -> None:
    container = get_container(container_name)
    try:
        container.delete_item(item=item_id, partition_key=partition_key)
    except Exception:
        logger.warning(f"Failed to delete item {item_id} from {container_name}")
