import requests
import json
from redis import Redis
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# endpoint = "https://api.mainnet-beta.solana.com"
endpoint = "https://solana-api.projectserum.com"

addresses = [
    "fArUAncZwVbMimiWv5cPUfFsapdLd8QMXZE4VXqFagR",
    "DmKR61BQk5zJTNCK9rrt8fM8HrDH6DSdE3Rt7sXKoAKb",
    "HoVhs7NAzcAaavr2tc2aaTynJ6kwhdfC2B2Z7EthKpeo",
    "85WdjCsxksAoCo6NNZSU4rocjUHsJwXrzpHJScg8oVNZ",
    "HuBBhoS81jyHTKMbhz8B3iYa8HSNShnRwXRzPzmFFuFr",
    "5unqG9sYX995czHCtHkkJvd2EaTE58jdvmjfz1nVvo5x",
    "Faszfxg7k2HWUT4CSGUn9MAVGUsPijvDQ3i2h7fi46M6",
    "G2zmxUhRGn12fuePJy9QsmJKem6XCRnmAEkf8G6xcRTj",
    "CvcqJtGdS9C1jKKFzgCi5p8qsnR5BZCohWvYMBJXcnJ8",
    "5fHS778vozoDDYzzJz2xYG39whTzGGW6bF71GVxRyMXi",
]

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

redis = Redis(host=REDIS_HOST, port=REDIS_PORT)


def get_redis_data(key):
    global redis
    get_data_index = 0
    get_data_flag = True
    return_data = ''
    while get_data_index < 2 and get_data_flag:
        try:
            return_data = redis.get(key)
            get_data_flag = False
        except:
            redis = redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
            get_data_index += 1
    return return_data if return_data else ''


def get_ray_supply():
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenSupply",
        "params": ["4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"],
    }

    response = requests.post(endpoint, json=data)

    return int(
        response.json()
        .get("result", {})
        .get("value", {})
        .get("amount", "555000000000000")
    )


def get_ray_balance(address):
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountBalance",
        "params": [address],
    }

    response = requests.post(endpoint, json=data)

    return int(
        response.json().get("result", {}).get("value", {}).get("amount", "0")
    )


@app.get("/ray/totalcoins", response_class=PlainTextResponse)
def totalcoins():
    return str(get_ray_supply() / 1e6)


@app.get("/ray/circulating", response_class=PlainTextResponse)
def circulating():
    circulating = get_ray_supply()

    for address in addresses:
        balance = get_ray_balance(address)
        circulating -= balance

    return str(circulating / 1e6)


@app.get("/ray/24_hour_volume", response_class=PlainTextResponse)
def get_ray_24_hour_volume():
    try:
        c = get_redis_data('size').decode('utf-8')
    except:
        c = ''
    return c


@app.get("/coin/price", response_class=PlainTextResponse)
def get_coin_price(coins: str):
    re_dict = {}
    try:
        coin_name = coins.split(',')
        re_dict = {}
        for item in coin_name:
            item_coin_name = f'{item}'.upper()
            item_price = get_redis_data(f'coin_price_{item_coin_name}')
            item_price_value = 0
            try:
                if item_price == '' and item_coin_name in ['USDT', 'USDC', 'USD']:
                    item_price_value = 1
                else:
                    item_price_value = json.loads(item_price)['value']
            except:
                pass
            re_dict[item_coin_name] = item_price_value
    except Exception as e:
        pass
    return json.dumps(re_dict)


@app.get("/pools", response_class=PlainTextResponse)
def get_pools():
    try:
        c = get_redis_data('tvl_and_apr').decode('utf-8')
    except:
        c = []
    return c



@app.get("/tvl", response_class=PlainTextResponse)
def get_tvl():
    try:
        c = get_redis_data('tvl')
    except:
        c = 0
    return c
