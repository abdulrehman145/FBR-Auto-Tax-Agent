from langchain_core.tools import tool
from app.services.stores import STORAGE

@tool
def storage_api(key: str, data: dict):
    STORAGE[key] = data
    return key
