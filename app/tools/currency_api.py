from langchain_core.tools import tool

@tool
def currency_api(amount: float, from_currency: str, to_currency: str):
    if from_currency == "USD" and to_currency == "PKR":
        return amount * 280
    return amount
