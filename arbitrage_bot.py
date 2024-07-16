import asyncio
import logging
import os
import time
from pybit.unified_trading import HTTP
from datetime import datetime
from dotenv import load_dotenv
import math

load_dotenv()

# Получение API-ключа из переменной окружения
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Проверка, что ключи были загружены корректно
if not BYBIT_API_KEY or not BYBIT_API_SECRET:
    raise ValueError("API keys not found. Please check your .env file.")


# Настройка сессии pybit
session = HTTP(
    testnet=False,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
)


# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logs/arbitrage_bot.log')
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_format = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# PAIRS = [
#     ('DOGEUSDT', 'DOGEUSDC'),
#     ('MNTUSDT', 'MNTUSDC'),
#     ('XRPUSDT', 'XRPUSDC'),
#     ('APEXUSDT', 'APEXUSDC'),
#     ('WLDUSDT', 'WLDUSDC'),
#     ('ADAUSDT', 'ADAUSDC'),
#     ('OPUSDT', 'OPUSDC'),
#     ('LDOUSDT', 'LDOUSDC')
# ]

# added all cryptopairs

PAIRS = [
    ('ADAUSDT', 'ADAUSDC'), ('APEUSDT', 'APEUSDC'), ('APEXUSDT', 'APEXUSDC'),
    ('APTUSDT', 'APTUSDC'), ('ARBUSDT', 'ARBUSDC'), ('CHZUSDT', 'CHZUSDC'),
    ('DOGEUSDT', 'DOGEUSDC'), ('DOTUSDT', 'DOTUSDC'), ('EOSUSDT', 'EOSUSDC'),
    ('FILUSDT', 'FILUSDC'), ('GMTUSDT', 'GMTUSDC'), ('HFTUSDT', 'HFTUSDC'),
    ('ICPUSDT', 'ICPUSDC'), ('LDOUSDT', 'LDOUSDC'), ('LUNCUSDT', 'LUNCUSDC'),
    ('MANAUSDT', 'MANAUSDC'), ('MATICUSDT', 'MATICUSDC'), ('MNTUSDT', 'MNTUSDC'),
    ('OPUSDT', 'OPUSDC'), ('SANDUSDT', 'SANDUSDC'), ('SEIUSDT', 'SEIUSDC'),
    ('SHIBUSDT', 'SHIBUSDC'), ('STRKUSDT', 'STRKUSDC'), ('SUIUSDT', 'SUIUSDC'),
    ('TRXUSDT', 'TRXUSDC'), ('USDEUSDT', 'USDEUSDC'), ('WLDUSDT', 'WLDUSDC'),
    ('XLMUSDT', 'XLMUSDC'), ('XRPUSDT', 'XRPUSDC'), ('ZKUSDT', 'ZKUSDC'), ('ZROUSDT', 'ZROUSDC'),
    ('BTCUSDT', 'BTCUSDC'), ('ETHUSDT', 'ETHUSDC')
]


def rounding(item: int | float, degree: int = 100) -> float:
    return math.floor(item * degree) / degree


async def fetch_ticker_info(session, pair, limit=3):
    try:
        data = session.get_orderbook(symbol=pair, category="spot", limit=limit)
        if 'result' in data and len(data['result']) > 0:
            bids = [(float(level[0]), float(level[1])) for level in data['result']['b']]
            asks = [(float(level[0]), float(level[1])) for level in data['result']['a']]
            return {
                'symbol': pair,
                'bids': bids,
                'asks': asks
            }
        else:
            logger.error(f"Error: No data in response for pair {pair}")
            return None
    except Exception as e:
        logger.error(f"Error fetching price data for pair {pair}: {str(e)}")
        return None


async def fetch_all_tickers_info(pairs, session):
    tasks = [fetch_ticker_info(session, pair) for pair in pairs]
    results = await asyncio.gather(*tasks)
    return {result['symbol']: result for result in results if result is not None}


def calculate_arbitrage_opportunities(prices, fee=0.001):
    start_time = time.time()
    logger.info("started to calc opportunities")
    opportunities = []

    if 'USDCUSDT' in prices:
        usdc_to_usdt_bids = prices['USDCUSDT']['bids']
        usdt_to_usdc_asks = prices['USDCUSDT']['asks']

        for pair1, pair2 in PAIRS:
            if pair1 in prices and pair2 in prices:
                usdt_asks = prices[pair1]['asks']
                usdc_bids = prices[pair2]['bids']

                # Расчет для направления USDT -> USDC
                if usdt_asks and usdc_bids and usdc_to_usdt_bids:
                    qty_usdt = 100
                    coins_buyed = 0
                    qty_usdc = 0
                    buy_orders_usdt = []

                    for ask_price, ask_volume in usdt_asks:
                        if qty_usdt <= 0:
                            break
                        trade_volume = min(qty_usdt / ask_price, ask_volume)
                        qty_usdt -= trade_volume * ask_price
                        coins_buyed += rounding(trade_volume * (1 - fee))
                        buy_orders_usdt.append((ask_price, rounding(trade_volume)))

                    # Шаг 2 - продажа монет за USDC
                    sell_orders_usdc = []

                    for bid_price, bid_volume in usdc_bids:
                        if coins_buyed <= 0:
                            break
                        trade_volume = min(coins_buyed, bid_volume)
                        coins_buyed -= trade_volume
                        qty_usdc += trade_volume * bid_price
                        sell_orders_usdc.append((bid_price, rounding(trade_volume)))

                    # Шаг 3 - продажа USDC за USDT
                    sell_orders_usdc_to_usdt = []
                    final_usdt = 0

                    for bid_price, bid_volume in usdc_to_usdt_bids:
                        if qty_usdc <= 0:
                            break
                        trade_volume = min(qty_usdc, bid_volume)
                        final_usdt += trade_volume * bid_price
                        qty_usdc -= trade_volume
                        sell_orders_usdc_to_usdt.append((bid_price, rounding(trade_volume)))

                    if final_usdt > 100:
                        final_usdt = rounding(final_usdt, degree=1000)
                        profit = rounding(final_usdt - 100, degree=1000)
                        opportunities.append({
                            'date': str(datetime.now()),
                            'pair1': pair1,
                            'pair2': pair2,
                            'direction': 'USDT -> USDC',
                            'buy_orders_usdt': buy_orders_usdt,
                            'sell_orders_usdc': sell_orders_usdc,
                            'sell_orders_usdc_to_usdt': sell_orders_usdc_to_usdt,
                            'final_usdt': final_usdt,
                            'profit': profit
                        })

                # Расчет для направления USDC -> USDT
                usdc_asks = prices[pair2]['asks']
                usdt_bids = prices[pair1]['bids']

                if usdc_asks and usdt_bids and usdt_to_usdc_asks:
                    qty_usdt = 100
                    qty_usdc = 0
                    coins_buyed = 0
                    buy_orders_usdt_to_usdc = []

                    # Шаг 1: Покупка USDC за USDT
                    for ask_price, ask_volume in usdt_to_usdc_asks:
                        if qty_usdt <= 0:
                            break
                        trade_volume = min(qty_usdt / ask_price, ask_volume)
                        qty_usdt -= trade_volume * ask_price
                        qty_usdc += rounding(trade_volume)
                        buy_orders_usdt_to_usdc.append((ask_price, rounding(trade_volume)))

                    # Шаг 2: Покупка монеты за USDC
                    buy_orders_usdc = []
                    for ask_price, ask_volume in usdc_asks:
                        if qty_usdc <= 0:
                            break
                        trade_volume = min(qty_usdc / ask_price, ask_volume)
                        qty_usdc -= trade_volume * ask_price
                        coins_buyed += rounding(trade_volume)
                        buy_orders_usdc.append((ask_price, rounding(trade_volume)))

                    # Шаг 3: Продажа монеты за USDT
                    sell_orders_usdt = []
                    final_usdt = 0
                    for bid_price, bid_volume in usdt_bids:
                        if coins_buyed <= 0:
                            break
                        trade_volume = min(coins_buyed, bid_volume)
                        final_usdt += trade_volume * bid_price * (1 - fee)
                        coins_buyed -= trade_volume
                        sell_orders_usdt.append((bid_price, rounding(trade_volume)))

                    if final_usdt > 100:
                        final_usdt = rounding(final_usdt, degree=1000)
                        profit = rounding(final_usdt - 100, degree=1000)
                        opportunities.append({
                            'date': str(datetime.now()),
                            'pair1': pair2,
                            'pair2': pair1,
                            'direction': 'USDC -> USDT',
                            'buy_orders_usdt_to_usdc': buy_orders_usdt_to_usdc,
                            'buy_orders_usdc': buy_orders_usdc,
                            'sell_orders_usdt': sell_orders_usdt,
                            'final_usdt': final_usdt,
                            'profit': profit
                        })

    end_time = time.time()
    logger.info(f"Time taken for calculating: {end_time - start_time} seconds")
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
    if usdt_balance < 100:
        logger.error("USDT balance is below 100. Stopping the bot.")
        return

    pair1 = opportunity['pair1']
    pair2 = opportunity['pair2']
    direction = opportunity['direction']
    fee = 0.001

    if direction == 'USDT -> USDC':
        buy_orders_usdt = opportunity['buy_orders_usdt']
        sell_orders_usdc = opportunity['sell_orders_usdc']
        sell_orders_usdc_to_usdt = opportunity['sell_orders_usdc_to_usdt']

        # Шаг 1: Покупка монеты за USDT
        buy_order_ids = []
        for price, volume in buy_orders_usdt:
            buy_order_id = place_order(pair1, 'Buy', volume, price, "Limit")
            buy_order_ids.append(buy_order_id)

        # Ожидание выполнения всех ордеров
        for buy_order_id in buy_order_ids:
            wait_for_order(pair1, buy_order_id)

        # Шаг 2: Продажа монеты за USDC
        sell_order_ids = []
        for price, volume in sell_orders_usdc:
            sell_order_id = place_order(pair2, 'Sell', volume, price, "Limit")
            sell_order_ids.append(sell_order_id)

        # Ожидание выполнения всех ордеров
        for sell_order_id in sell_order_ids:
            wait_for_order(pair2, sell_order_id)

        # Шаг 3: Продажа USDC за USDT
        sell_usdc_order_ids = []
        for price, volume in sell_orders_usdc_to_usdt:
            sell_usdc_order_id = place_order('USDCUSDT', 'Sell', volume, price, "Limit")
            sell_usdc_order_ids.append(sell_usdc_order_id)

        # Ожидание выполнения всех ордеров
        for sell_usdc_order_id in sell_usdc_order_ids:
            wait_for_order('USDCUSDT', sell_usdc_order_id)

    elif direction == 'USDC -> USDT':
        buy_orders_usdt_to_usdc = opportunity['buy_orders_usdt_to_usdc']
        buy_orders_usdc = opportunity['buy_orders_usdc']
        sell_orders_usdt = opportunity['sell_orders_usdt']

        # Шаг 1: Покупка USDC за USDT
        buy_usdc_order_ids = []
        for price, volume in buy_orders_usdt_to_usdc:
            buy_usdc_order_id = place_order('USDCUSDT', 'Buy', volume, price, "Limit")
            buy_usdc_order_ids.append(buy_usdc_order_id)

        # Ожидание выполнения всех ордеров
        for buy_usdc_order_id in buy_usdc_order_ids:
            wait_for_order('USDCUSDT', buy_usdc_order_id)

        # Проверяем баланс USDC после покупки
        usdc_balance = get_balance('USDC')

        # Шаг 2: Покупка монеты за USDC
        buy_order_ids = []
        for price, volume in buy_orders_usdc:
            if usdc_balance <= 0:
                break
            trade_volume = min(usdc_balance / price, volume)
            buy_order_id = place_order(pair1, 'Buy', trade_volume, price, "Limit")
            buy_order_ids.append(buy_order_id)
            usdc_balance -= trade_volume * price

        # Ожидание выполнения всех ордеров
        for buy_order_id in buy_order_ids:
            wait_for_order(pair1, buy_order_id)

        # Проверяем баланс монеты после покупки
        coin_balance = get_balance(pair1[:-4])

        # Шаг 3: Продажа монеты за USDT
        sell_order_ids = []
        for price, volume in sell_orders_usdt:
            if coin_balance <= 0:
                break
            trade_volume = min(coin_balance, volume)
            sell_order_id = place_order(pair2, 'Sell', trade_volume, price, "Limit")
            sell_order_ids.append(sell_order_id)
            coin_balance -= trade_volume

        # Ожидание выполнения всех ордеров
        for sell_order_id in sell_order_ids:
            wait_for_order(pair2, sell_order_id)


async def main():
    logger.info("Starting to calculate arbitrage opportunities")
    while True:
        pairs_to_fetch = [pair for pair1, pair2 in PAIRS for pair in [pair1, pair2]]
        pairs_to_fetch.append('USDCUSDT')  # добавляем пару для конвертации USDC в USDT
        prices = await fetch_all_tickers_info(pairs_to_fetch, session)
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
