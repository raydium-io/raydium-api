import json
from distutils.version import StrictVersion

import requests
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from redis import Redis

from setting import *

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

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS)


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
            redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS)
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
    c = get_redis_data('size').decode('utf-8')
    return c


@app.get("/coin/price", response_class=JSONResponse)
def get_coin_price(coins: str = ''):
    re_dict = {}
    try:
        if coins == '' or coins == 'SOL,WSOL,BTC,ETH,USDT,WUSDT,USDC,WUSDC,YFI,LINK,XRP,SUSHI,ALEPH,SXP,HGET,CREAM,UBXT,HNT,FRONT,AKRO,HXRO,UNI,SRM,FTT,MSRM,TOMO,KARMA,LUA,MATH,KEEP,SWAG,FIDA,KIN,MAPS,OXY,RAY,COPE,STEP,MEDIA':
            re_dict = json.loads(get_redis_data(f'coin_price:ray_default'))
        else:
            coin_name = coins.split(',')
            re_dict = {}
            for item in coin_name:
                item_coin_name = f'{item}'.upper()
                item_price = get_redis_data(f'coin_price:{item_coin_name}')
                item_price_value = 0
                try:
                    if item_price == '' and item_coin_name in ['USDT', 'USDC', 'USD', 'WUSDT', 'WUSDC', 'WUSD']:
                        item_price_value = 1
                    else:
                        item_price_value = json.loads(item_price)['value']
                except:
                    pass
                re_dict[item_coin_name] = item_price_value
    except Exception as e:
        pass
    return re_dict


@app.get("/pools", response_class=JSONResponse)
def get_pools():
    c = json.loads(get_redis_data('tvl_and_apr'))
    return c


@app.get("/tvl", response_class=PlainTextResponse)
def get_tvl():
    c = get_redis_data('tvl')
    return c


@app.get("/pairs", response_class=JSONResponse)
def get_pairs():
    c = json.loads(get_redis_data('fills_data'))
    return c


@app.get("/info", response_class=JSONResponse)
def get_info(response: Response):
    tvl = 0
    volume24h = 0
    try:
        tvl = round(float(get_redis_data('tvl')), 2)
        volume24h = round(float(get_redis_data('size').decode('utf-8')), 2)
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        tvl = 0
        volume24h = 0
    return {
        'tvl': tvl,
        'volume24h': volume24h
    }


@app.get("/config", response_class=JSONResponse)
def get_config(v: str, response: Response):
    try:
        rpc_list = json.loads(get_redis_data('config_rpc_list'))
        success = StrictVersion(get_redis_data('config_version').decode('utf-8')) <= StrictVersion(v)
    except json.decoder.JSONDecodeError as e:
        rpc_list = []
        success = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    except ValueError as e:
        rpc_list = []
        success = False
        response.status_code = status.HTTP_400_BAD_REQUEST
    except Exception as e:
        rpc_list = []
        success = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        'rpcs': rpc_list,
        'success': success,
    }
