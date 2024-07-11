import aiohttp
import asyncio
import logging
import os
import time
from pybit.unified_trading import HTTP
import certifi
import ssl
from datetime import datetime
from dotenv import load_dotenv
import math

load_dotenv()

# Получение API-ключа из переменной окружения
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_SECRET_KEY')

# Настройка сессии pybit
session = HTTP(
    testnet=False,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
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
console_format = logging.Formatter('%(asctime)s - %(message)s')
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
    ssl_context = ssl.create_default_context(cafile=certifi.where())
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

                # Расчет для направления USDT -> USDC
                if buy_price_usdt and sell_price_usdc and usdc_to_usdt_sell_price:
                    # Количество монет, которые мы можем купить на 1000 USDT с учетом комиссии и округлением вниз
                    qty_after_buy_fee = (100 / buy_price_usdt) * (1 - fee)
                    qty_after_buy_fee = math.floor(qty_after_buy_fee * 100) / 100  # Округление вниз до сотых

                    # Количество USDC после продажи с вычетом комиссии и округлением вниз
                    usdc_after_sell_fee = (qty_after_buy_fee * sell_price_usdc) * (1 - fee)
                    usdc_after_sell_fee = math.floor(usdc_after_sell_fee * 100) / 100  # Округление вниз до сотых

                    # Конвертация USDC обратно в USDT с вычетом комиссии и округлением вниз
                    final_usdt = usdc_after_sell_fee * usdc_to_usdt_sell_price

                    if final_usdt > 100:
                        profit = final_usdt - 100
                        opportunities.append({
                            'date': str(datetime.now()),
                            'pair1': pair1,
                            'pair2': pair2,
                            'direction': 'USDT -> USDC',
                            'buy_price': buy_price_usdt,
                            'sell_price': sell_price_usdc,
                            'usdc_to_usdt_sell_price': usdc_to_usdt_sell_price,
                            'qty_after_buy_fee': qty_after_buy_fee,
                            'usdc_after_sell_fee': usdc_after_sell_fee,
                            'final_usdt': final_usdt,
                            'profit': profit
                        })

                # Расчет для направления USDC -> USDT
                buy_price_usdc = prices[pair2]['ask_price']
                sell_price_usdt = prices[pair1]['bid_price']

                if buy_price_usdc and sell_price_usdt and usdt_to_usdc_buy_price:
                    # Количество монет, которые мы можем купить на 1000 USDC с учетом комиссии и округлением вниз
                    qty_after_buy_fee = (100 / buy_price_usdc) * (1 - fee)
                    qty_after_buy_fee = math.floor(qty_after_buy_fee * 100) / 100  # Округление вниз до сотых

                    # Количество USDT после продажи с вычетом комиссии и округлением вниз
                    usdt_after_sell_fee = (qty_after_buy_fee * sell_price_usdt) * (1 - fee)
                    usdt_after_sell_fee = math.floor(usdt_after_sell_fee * 100) / 100  # Округление вниз до сотых

                    # Конвертация USDT обратно в USDC (без комиссии на конвертацию USDCUSDT)
                    final_usdc = usdt_after_sell_fee / usdt_to_usdc_buy_price

                    if final_usdc > 100:
                        profit = final_usdc - 100
                        opportunities.append({
                            'date': str(datetime.now()),
                            'pair1': pair2,
                            'pair2': pair1,
                            'direction': 'USDC -> USDT',
                            'buy_price': buy_price_usdc,
                            'sell_price': sell_price_usdt,
                            'usdt_to_usdc_buy_price': usdt_to_usdc_buy_price,
                            'qty_after_buy_fee': qty_after_buy_fee,
                            'usdt_after_sell_fee': usdt_after_sell_fee,
                            'final_usdc': final_usdc,
                            'profit': profit
                        })

    return opportunities


def write_opportunities_to_file(opportunities, filename="arbitrage_opportunities.txt"):
    with open(filename, 'a') as f:
        for opp in opportunities:
            f.write(f"Arbitrage opportunity found! {opp}\n")


def get_balance(coin):
    """
    Connects via API to Bybit, gets balance for the given coin, and returns a float value.
    """
    balance = session.get_wallet_balance(
        accountType="UNIFIED",
        coin=coin
    )['result']['list'][0]['coin'][0]['equity']

    return float(balance)


def place_order(symbol, side, qty, price, order_type, time_in_force="GTC"):
    """
    Places an order via Bybit API.

    Args:
    - symbol (str): The trading pair symbol (e.g., 'XRPUSDT').
    - side (str): The order side, either 'Buy' or 'Sell'.
    - qty (float): The quantity to buy or sell.
    - price (float): The limit price for the order.
    - time_in_force (str): Time in force policy (default is "GTC").

    Returns:
    - str: The order ID of the placed order.
    """
    order = session.place_order(
        category="spot",
        symbol=symbol,
        side=side,
        # order_type="Limit",
        order_type=order_type,
        qty=qty,
        price=price,
        time_in_force=time_in_force
    )
    order_id = order['result']['orderId']
    print(f"{side} Order placed: {order_id} for {symbol} at {price}")
    return order_id


def wait_for_order(symbol, order_id):
    """
    Waits for an order to be filled via Bybit API.

    Args:
    - symbol (str): The trading pair symbol (e.g., 'XRPUSDT').
    - order_id (str): The ID of the order to wait for.
    """
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
    """
    Executes the arbitrage opportunity.

    Args:
    - opportunity (dict): The arbitrage opportunity details.
    """
    # Проверяем баланс USDT перед началом арбитража
    usdt_balance = get_balance('USDT')
    if usdt_balance < 70:
        logger.error("USDT balance is below 70. Stopping the bot.")
        exit()

    pair1 = opportunity['pair1']
    pair2 = opportunity['pair2']
    direction = opportunity['direction']
    buy_price = opportunity['buy_price']
    sell_price = opportunity['sell_price']
    usdc_to_usdt_sell_price = opportunity.get('usdc_to_usdt_sell_price', 1)
    qty = math.floor((100 / buy_price) * 100) / 100  # Количество для покупки на 100 USDT, округленное вниз до сотых
    fee = 0.001

    if direction == 'USDT -> USDC':
        # Шаг 1: Покупка за USDT
        buy_order_id = place_order(pair1, 'Buy', qty, buy_price, "Limit")
        wait_for_order(pair1, buy_order_id)

        # Учитываем комиссию после покупки
        qty_after_buy_fee = math.floor((qty * (1 - fee)) * 100) / 100

        # Шаг 2: Продажа за USDC
        sell_order_id = place_order(pair2, 'Sell', qty_after_buy_fee, sell_price, "Limit")
        wait_for_order(pair2, sell_order_id)

        # Учитываем комиссию после продажи
        usdc_balance = math.floor((qty_after_buy_fee * sell_price * (1 - fee)) * 100) / 100

        # Шаг 3: Продажа USDC за USDT
        if usdc_balance > 0:
            sell_usdc_order_id = place_order('USDCUSDT', 'Sell', usdc_balance, usdc_to_usdt_sell_price, "Limit")
            wait_for_order('USDCUSDT', sell_usdc_order_id)

    elif direction == 'USDC -> USDT':
        # Шаг 1: Покупка USDC за USDT
        buy_usdc_order_id = place_order('USDCUSDT', 'Buy', qty, usdc_to_usdt_sell_price, "Limit")
        wait_for_order('USDCUSDT', buy_usdc_order_id)

        # Учитываем комиссию после покупки
        usdc_balance = math.floor((qty * (1 - fee)) * 100) / 100

        # Шаг 2: Покупка пары2 за USDC
        buy_order_id = place_order(pair2, 'Buy', usdc_balance, buy_price, "Limit")
        wait_for_order(pair2, buy_order_id)

        # Учитываем комиссию после покупки
        qty_after_buy_fee = math.floor((usdc_balance / buy_price * (1 - fee)) * 100) / 100

        # Шаг 3: Продажа пары2 за USDT
        sell_order_id = place_order(pair1, 'Sell', qty_after_buy_fee, sell_price, "Limit")
        wait_for_order(pair1, sell_order_id)


async def main():
    logger.info("Starting to calculate arbitrage opportunities")
    while True:
        pairs_to_fetch = [pair for pair1, pair2 in PAIRS for pair in [pair1, pair2]]
        pairs_to_fetch.append('USDCUSDT')  # добавляем пару для конвертации USDC в USDT
        prices = await fetch_all_tickers_info(pairs_to_fetch, BYBIT_API_KEY)
        logger.info(f"Fetched prices: {prices}")

        opportunities = calculate_arbitrage_opportunities(prices)
        if opportunities:
            logger.error(f"Arbitrage opportunities found: {opportunities}")
            write_opportunities_to_file(opportunities)
            for opportunity in opportunities:
                execute_arbitrage(opportunity)

        await asyncio.sleep(1)


if __name__ == '__main__':
    logger.info("Bot has been started")
    asyncio.run(main())
