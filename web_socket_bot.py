import aiohttp
import asyncio
import logging
import ssl
import certifi
import os
import json
import websockets
import time
from pybit import spot

# Получение API-ключа из переменной окружения
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Подключение к Bybit Spot API
session = spot.HTTP(
    endpoint="https://api.bybit.com",
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('arbitrage_bot.log')
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_format = logging.Formatter('%(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

PAIRS = [
    ('DOGEUSDT', 'DOGEUSDC'),
    ('MNTUSDT', 'MNTUSDC'),
    ('XRPUSDT', 'XRPUSDC'),
    ('APEXUSDT', 'APEXUSDC'),
    ('WLDUSDT', 'WLDUSDC'),
    ('ADAUSDT', 'ADAUSDC'),
    ('OPUSDT', 'OPUSDC'),
    ('LDOUSDT', 'LDOUSDC')
]

async def fetch_ticker_info(session, url, headers):
    try:
        async with session.get(url, headers=headers, ssl=False) as response:
            data = await response.json()
            if 'result' in data and len(data['result']['list']) > 0:
                ticker_info = data['result']['list'][0]
                return {
                    'symbol': ticker_info['symbol'],
                    'bid_price': float(ticker_info['bid1Price']),
                    'ask_price': float(ticker_info['ask1Price'])
                }
            else:
                logger.error(f"Error: No data in response for {url}")
                return None
    except Exception as e:
        logger.error(f"Error fetching price data: {str(e)}")
        return None

async def fetch_all_tickers_info(pairs, api_key):
    headers = {"X-API-KEY": api_key}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for pair in pairs:
            url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={pair}"
            tasks.append(fetch_ticker_info(session, url, headers))
        results = await asyncio.gather(*tasks)
        return {result['symbol']: result for result in results if result is not None}

def calculate_arbitrage_opportunities(prices, fee=0.001):
    opportunities = []
    if 'USDCUSDT' in prices:
        usdc_to_usdt_sell_price = prices['USDCUSDT']['bid_price']
        usdt_to_usdc_buy_price = prices['USDCUSDT']['ask_price']
        for pair1, pair2 in PAIRS:
            if pair1 in prices and pair2 in prices:
                buy_price_usdt = prices[pair1]['ask_price']
                sell_price_usdc = prices[pair2]['bid_price']
                if buy_price_usdt and sell_price_usdc and usdc_to_usdt_sell_price:
                    effective_buy_price_usdt = buy_price_usdt * (1 + fee)
                    effective_sell_price_usdc = sell_price_usdc * (1 - fee)
                    final_sell_price_in_usdt = effective_sell_price_usdc * usdc_to_usdt_sell_price

                    if effective_buy_price_usdt < final_sell_price_in_usdt:
                        profit = (final_sell_price_in_usdt / effective_buy_price_usdt) - 1
                        opportunities.append({
                            'pair1': pair1,
                            'pair2': pair2,
                            'direction': 'USDT -> USDC',
                            'buy_price': buy_price_usdt,
                            'sell_price': sell_price_usdc,
                            'usdc_to_usdt_sell_price': usdc_to_usdt_sell_price,
                            'effective_buy_price': effective_buy_price_usdt,
                            'effective_sell_price': effective_sell_price_usdc,
                            'final_sell_price_in_usdt': final_sell_price_in_usdt,
                            'profit': profit
                        })

                buy_price_usdc = prices[pair2]['ask_price']
                sell_price_usdt = prices[pair1]['bid_price']
                if buy_price_usdc and sell_price_usdt and usdt_to_usdc_buy_price:
                    effective_buy_price_usdc = buy_price_usdc * (1 + fee)
                    effective_sell_price_usdt = sell_price_usdt * (1 - fee)
                    final_sell_price_in_usdt = effective_sell_price_usdt * (1 / usdt_to_usdc_buy_price)

                    if effective_buy_price_usdc < final_sell_price_in_usdt:
                        profit = (final_sell_price_in_usdt / effective_buy_price_usdc) - 1
                        opportunities.append({
                            'pair1': pair2,
                            'pair2': pair1,
                            'direction': 'USDC -> USDT',
                            'buy_price': buy_price_usdc,
                            'sell_price': sell_price_usdt,
                            'usdt_to_usdc_buy_price': usdt_to_usdc_buy_price,
                            'effective_buy_price': effective_buy_price_usdc,
                            'effective_sell_price': effective_sell_price_usdt,
                            'final_sell_price_in_usdt': final_sell_price_in_usdt,
                            'profit': profit
                        })

    return opportunities

def place_order(symbol, side, qty, price, time_in_force="GTC"):
    order = session.place_order(
        category="spot",
        symbol=symbol,
        side=side,
        order_type="Limit",
        qty=qty,
        price=price,
        time_in_force=time_in_force
    )
    order_id = order['result']['orderId']
    print(f"{side} Order placed: {order_id} for {symbol} at {price}")
    return order_id

def wait_for_order(symbol, order_id):
    while True:
        order_status = session.get_open_orders(
            category="spot",
            symbol=symbol,
            orderId=order_id
        )['result']['list']

        if order_status and order_status[0]['orderStatus'] == 'Filled':
            print(f"Order filled: {order_id}")
            break
        else:
            print(f"Waiting for order {order_id} to be filled...")
            time.sleep(0.1)  # Ждем 0.1 секунд перед повторной проверкой

def execute_arbitrage(opportunity):
    pair1 = opportunity['pair1']
    pair2 = opportunity['pair2']
    buy_price = opportunity['buy_price']
    sell_price = opportunity['sell_price']
    direction = opportunity['direction']

    qty = 1000 / buy_price  # Количество монет для покупки на 1000 USDT

    if direction == 'USDT -> USDC':
        buy_order_id = place_order(pair1, 'Buy', qty, buy_price)
        wait_for_order(pair1, buy_order_id)
        sell_order_id = place_order(pair2, 'Sell', qty, sell_price)
        wait_for_order(pair2, sell_order_id)
    elif direction == 'USDC -> USDT':
        buy_order_id = place_order(pair2, 'Buy', qty, buy_price)
        wait_for_order(pair2, buy_order_id)
        sell_order_id = place_order(pair1, 'Sell', qty, sell_price)
        wait_for_order(pair1, sell_order_id)

async def main():
    uri = "wss://stream.bybit.com/realtime"

    async with websockets.connect(uri) as websocket:
        subscribe_message = {
            "op": "subscribe",
            "args": [f"orderBookL2_25.{pair1}" for pair1, pair2 in PAIRS] + [f"orderBookL2_25.{pair2}" for pair1, pair2 in PAIRS]
        }
        await websocket.send(json.dumps(subscribe_message))

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if 'data' in data:
                prices = {}
                for update in data['data']:
                    symbol = update['symbol']
                    prices[symbol] = {
                        'bid_price': float(update['bids'][0][0]),
                        'ask_price': float(update['asks'][0][0])
                    }

                opportunities = calculate_arbitrage_opportunities(prices)
                if opportunities:
                    print(f"Arbitrage opportunities found: {opportunities}")
                    for opportunity in opportunities:
                        execute_arbitrage(opportunity)

if __name__ == '__main__':
    asyncio.run(main())
