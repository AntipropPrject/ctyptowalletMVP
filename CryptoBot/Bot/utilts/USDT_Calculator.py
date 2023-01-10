import json

import requests


class USDT_Calculator:
    def __init__(self):
        self.api_ulr = "https://api.binance.com/api/v1/ticker/24hr?symbol="

    def calculate(self, amount:float, token_name: str) -> float:
        ticker_name = f"{token_name.upper()}USDT" #TRXUSDT
        response = requests.get(f"{self.api_ulr}{ticker_name}") #https://api.binance.com/api/v1/ticker/24hr?symbol=USDTTRX
        response_json = response.text
        last_price:float = self.__get_lastprice_from_response(response_json)

        result = amount*last_price
        print(result)
        return result


    def __get_lastprice_from_response(self, response_json:str):
        response_dict: dict[str, str] = json.loads(response_json)
        value = response_dict["lastPrice"]
        return float(value)


# USDT_Calculator().calculate(10, "btc")



