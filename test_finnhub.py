import requests

FINNHUB_API_KEY = "d7ntn5hr01qs975tf2r0d7ntn5hr01qs975tf2rg"
symbol = "AAPL"

url = "https://finnhub.io/api/v1/stock/recommendation"
params = {"symbol": symbol, "token": FINNHUB_API_KEY}

response = requests.get(url, params=params)
data = response.json()

print(data)