import requests

# Bybit API endpoint
base_url = "https://api.bybit.com"

# Получение списка всех доступных торговых пар
def get_all_symbols():
    url = f"{base_url}/v5/market/tickers?category=spot"
    response = requests.get(url)
    data = response.json()
    return data

# Фильтрация торговых пар, чтобы оставить только те, которые имеют вид {монета}USDT и {монета}USDC
def filter_usdt_usdc_pairs(symbols):
    usdt_pairs = set()
    usdc_pairs = set()

    for symbol_data in symbols:
        symbol = symbol_data['symbol']
        if symbol.endswith("USDT"):
            usdt_pairs.add(symbol.replace("USDT", ""))
        elif symbol.endswith("USDC"):
            usdc_pairs.add(symbol.replace("USDC", ""))

    # Пересечение двух множеств, чтобы оставить только те монеты, которые имеют обе пары
    common_pairs = usdt_pairs.intersection(usdc_pairs)
    return common_pairs

# Получение текущих цен для пары
def get_current_price(symbol):
    url = f"{base_url}/v5/market/tickers?category=spot&symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    if 'result' in data and 'list' in data['result'] and len(data['result']['list']) > 0:
        return float(data['result']['list'][0]['lastPrice'])
    return None

# Главная функция
def main():
    symbols_data = get_all_symbols()
    if 'result' in symbols_data and 'list' in symbols_data['result']:
        symbols = symbols_data['result']['list']
        common_pairs = filter_usdt_usdc_pairs(symbols)

        filtered_pairs = []
        for pair in common_pairs:
            usdt_pair = f"{pair}USDT"
            price = get_current_price(usdt_pair)
            if price and price <= 10:
                filtered_pairs.append(pair)

        print(f"Активы с парами вида {{монета}}USDT и {{монета}}USDC, цена которых не превышает 10$: {sorted(filtered_pairs)}")
    else:
        print("Не удалось получить список торговых пар.")

if __name__ == "__main__":
    main()
