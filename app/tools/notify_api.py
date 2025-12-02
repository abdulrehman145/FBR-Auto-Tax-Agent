from langchain_core.tools import tool

@tool
def notify_api(message: str):
    print("NOTIFY:", message)
