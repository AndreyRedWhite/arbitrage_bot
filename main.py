import os
from dotenv import load_dotenv

from pybit.unified_trading import HTTP
from pprint import pprint
import time

load_dotenv()

# Получение API-ключа из переменной окружения
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_SECRET_KEY = os.getenv('BYBIT_SECRET_KEY')

session = HTTP(
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_SECRET_KEY,
    testnet=False
)


def get_balance(coin):
    """
    connects via api to bybit, gets balance for given, return a float value
    """
    balance = session.get_wallet_balance(
        accountType="UNIFIED",
        coin=coin
    )['result']['list'][0]['coin'][0]['equity']

    return float(balance)


def place_sell_order(symbol, qty, price):
    """

    :param symbol: string - Symbol name, like BTCUSDT, uppercase only
    :param qty: string - Order quantity
    :param price: string - Order price
    :return:
    """
    order = session.place_order(
        category="spot",
        symbol=symbol,
        side="Sell",
        order_type="Limit",
        qty=qty,
        price=price,
        # time_in_force="IOC"
    )
    return order


def place_buy_order(symbol, qty, price):
    order = session.place_order(
        category="spot",
        symbol=symbol,
        side="Buy",
        order_type="Limit",
        qty=qty,
        price=price,
        # time_in_force="IOC"
    )
    return order


def get_instrument_info(symbol):
    """
    returns data with this parameters:
    >> maxOrderQty - Maximum quantity for Limit and PostOnly order
    >> maxMktOrderQty - Maximum quantity for Market order
    >> minOrderQty - Minimum order quantity
    >> minNotionalValue	- Minimum notional value
    >> qtyStep - The step to increase/reduce order quantity
    >> postOnlyMaxOrderQty - depricated
    """

    coin_data = session.get_instruments_info(
        category="spot",
        symbol=symbol
    )["result"]["list"][0]["lotSizeFilter"]
    return coin_data


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


def arbitrage_xrp(buy_price_usdt, sell_price_usdc, sell_price_usdt):
    qty = 3  # Количество, замените на актуальное значение

    # Шаг 1: Покупка XRP за USDT
    buy_order_id = place_order('XRPUSDT', 'Buy', 2.66, buy_price_usdt)
    wait_for_order('XRPUSDT', buy_order_id)

    # Шаг 2: Продажа XRP за USDC
    sell_order_id = place_order('XRPUSDC', 'Sell', 2.66, sell_price_usdc)
    wait_for_order('XRPUSDC', sell_order_id)

    # Шаг 3: Продажа USDC за USDT
    sell_usdc_order_id = place_order('USDCUSDT', 'Sell', 1, sell_price_usdt)
    wait_for_order('USDCUSDT', sell_usdc_order_id)


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
                    final_sell_price_in_usdt = effective_sell_price_usdc * usdc_to_usdt_sell_price * (1 - fee)

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
                    final_sell_price_in_usdt = effective_sell_price_usdt * (1 / usdt_to_usdc_buy_price) * (1 - fee)

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



if __name__ == '__main__':
    # pprint(get_balance("USDC"), width=200)
    # pprint(get_balance("USDT"), width=200)
    # pprint(get_instrument_info("NOTUSDT"))
    # place_sell_order('NOTUSDT', "100",
    # "0.014760")
    # print(place_sell_order('NOTUSDT', "100", "0.014520"))

    # print((place_buy_order("XRPUSDT", "2.63", "0.4247")))
    buy_price_usdt = 0.4212  # Замените на актуальную цену покупки
    sell_price_usdc = 0.4204  # Замените на актуальную цену продажи
    sell_price_usdt = 1  # Замените на актуальную цену продажи USDC за USDT
    arbitrage_xrp(buy_price_usdt, sell_price_usdc, sell_price_usdt)

