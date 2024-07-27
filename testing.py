import math


def rounding(item: float, degree: int = 100) -> float:
    """
    Функция для округления чисел в меньшую сторону. По дефолту округляет до сотых.
    Нужна для корректного расчета баланса полученых монет (их не может быть больше как при арифметическом округлении)
    :param item (float): число для округления
    :param degree (int): степень округления
    :return:
    float - возвращает результат
    """
    return math.floor(item * degree) / degree


def rounding_price(price, decimals=4):
    return round(price, decimals)


def calculate_arbitrage_opportunities(prices=None, fee=0.001):
    opportunities = []

    usdc_to_usdt_bids = [(1.0, 3930658.17), (0.9999, 3185806.05), (0.9998, 1341984.28)]
    usdt_to_usdc_asks = [(1.0001, 4808882.01), (1.0002, 432756.94), (1.0003, 362054.48)]

    usdt_asks = [(0.3443, 615.17), (0.3444, 614.76), (0.3445, 2177.76)]
    usdc_bids = [(0.3449, 15.53), (0.3448, 521.77), (0.3447, 23.04)]


    if usdt_asks and usdc_bids and usdc_to_usdt_bids:
        qty_usdt = 100
        coins_buyed = 0
        qty_usdc = 0
        buy_orders_usdt = []
        print("-------------FIRST STEP------------")
        print("Buy coins for USDT")
        for ask_price, ask_volume in usdt_asks:
            print(f"Checking USDT qty. It is: {qty_usdt}")
            if rounding(qty_usdt) <= 0:
                print("stop iteration\n")
                break
            trade_volume = (min(qty_usdt / ask_price, ask_volume))
            print(f"calculated trade volume: {trade_volume}")

            qty_usdt -= (trade_volume * ask_price)
            print(f"new qty_usdt is: {qty_usdt}")

            coins_buyed += rounding(rounding(trade_volume) * (1 - fee))
            print(f"this is coins_buyed: {coins_buyed}")
            if rounding(trade_volume) > 0:
                buy_orders_usdt.append((rounding_price(ask_price), rounding(trade_volume)))
                print(f"new order for buying usdt: ({rounding_price(ask_price)}, {rounding(trade_volume)})")
        print("---------STEP2---------")
        print("sell coins for USDC")
        # Шаг 2 - продажа монет за USDC
        sell_orders_usdc = []

        for bid_price, bid_volume in usdc_bids:
            print("check before next iteration")
            print(f"Checking current coins. It is {coins_buyed}\n")
            if coins_buyed <= 0:
                print("stop iteration iteration\n")
                break
            trade_volume = min(coins_buyed, bid_volume)
            print(f"trade volume for COIN->USDC is {trade_volume}")

            if rounding(trade_volume) > 0:
                coins_buyed -= rounding(trade_volume)
                print(f"Coins left is: {coins_buyed}")

                qty_usdc += trade_volume * bid_price
                print(f"new qty_usdc: {qty_usdc}")

                sell_orders_usdc.append((rounding_price(bid_price), rounding(trade_volume)))
                print(f"new sell order is:({rounding_price(bid_price)}, {rounding(trade_volume)})")
        print("--------STEP3------------")
        print("sell USDC for USDT\n")
        # Шаг 3 - продажа USDC за USDT
        sell_orders_usdc_to_usdt = []
        final_usdt = 0
        print(f"final usdt now is: {final_usdt}")

        for bid_price, bid_volume in usdc_to_usdt_bids:
            if qty_usdc <= 0:
                print(f"checking usdc qty. Now it is: {qty_usdc}")
                break
            trade_volume = min(qty_usdc, bid_volume)
            print(f"calculating trade volume. Now it is: {trade_volume}")
            if rounding(trade_volume) > 0:
                final_usdt += trade_volume * bid_price
                print(f"this is the current final_usdt: {final_usdt}")
                qty_usdc -= trade_volume
                print(f"this is current usdc qty: {qty_usdc}")
                sell_orders_usdc_to_usdt.append((rounding_price(bid_price), rounding(trade_volume)))
                print(f"sell orders for usdc to usdt is ({rounding_price(bid_price)}, {rounding(trade_volume)})")
        if final_usdt > 100:
            final_usdt = rounding(final_usdt, degree=1000)
            print(f"final usdt is: {final_usdt}")
            profit = rounding(final_usdt - 100, degree=1000)
            print(f"profit is: {profit}")
    print("\nfinal result")
    print(f"{buy_orders_usdt=}")
    print(f"{sell_orders_usdc=}")
    print(f"{sell_orders_usdc_to_usdt=}")
    # # Расчет для направления USDC -> USDT
    # usdc_asks = prices[pair2]['asks']
    # usdt_bids = prices[pair1]['bids']
    #
    # if usdc_asks and usdt_bids and usdt_to_usdc_asks:
    #     qty_usdt = 100
    #     qty_usdc = 0
    #     coins_buyed = 0
    #     buy_orders_usdt_to_usdc = []
    #
    #     # Шаг 1: Покупка USDC за USDT
    #     for ask_price, ask_volume in usdt_to_usdc_asks:
    #         if qty_usdt <= 0:
    #             break
    #         trade_volume = min(qty_usdt / ask_price, ask_volume)
    #         qty_usdt -= trade_volume * ask_price
    #         qty_usdc += rounding(trade_volume)
    #         if rounding(trade_volume) > 0:
    #             buy_orders_usdt_to_usdc.append((rounding_price(ask_price), rounding(trade_volume)))
    #
    #     # Шаг 2: Покупка монеты за USDC
    #     buy_orders_usdc = []
    #     for ask_price, ask_volume in usdc_asks:
    #         if qty_usdc <= 0:
    #             break
    #         trade_volume = min(qty_usdc / ask_price, ask_volume)
    #         qty_usdc -= trade_volume * ask_price
    #         coins_buyed += rounding(trade_volume)
    #         if rounding(trade_volume) > 0:
    #             buy_orders_usdc.append((rounding_price(ask_price), rounding(trade_volume)))
    #
    #     # Шаг 3: Продажа монеты за USDT
    #     sell_orders_usdt = []
    #     final_usdt = 0
    #     for bid_price, bid_volume in usdt_bids:
    #         if coins_buyed <= 0:
    #             break
    #         trade_volume = min(coins_buyed, bid_volume)
    #         final_usdt += trade_volume * bid_price * (1 - fee)
    #         coins_buyed -= trade_volume
    #         if rounding(trade_volume) > 0:
    #             sell_orders_usdt.append((rounding_price(bid_price), rounding(trade_volume)))
    #
    #     if final_usdt > 100:
    #         final_usdt = rounding(final_usdt, degree=1000)
    #         profit = rounding(final_usdt - 100, degree=1000)
    #         opportunities.append({
    #             'date': str(datetime.now()),
    #             'pair1': pair2,
    #             'pair2': pair1,
    #             'direction': 'USDC -> USDT',
    #             'buy_orders_usdt_to_usdc': buy_orders_usdt_to_usdc,
    #             'buy_orders_usdc': buy_orders_usdc,
    #             'sell_orders_usdt': sell_orders_usdt,
    #             'final_usdt': final_usdt,
    #             'profit': profit
    #         })
    #
    # end_time = time.time()
    # logger.info(f"Time taken for calculating: {end_time - start_time} seconds")
    # return opportunities
if __name__ == '__main__':
    calculate_arbitrage_opportunities()