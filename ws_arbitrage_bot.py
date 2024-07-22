from pybit.unified_trading import WebSocket
from time import sleep


def main():
    ws = WebSocket(
        testnet=False,
        channel_type='spot',
    )

    def handle_message(message):
        print(message)

    ws.ticker_stream(
        symbol='APEXUSDT',
        callback=handle_message,
    )

    while True:
        sleep(1)


if __name__ == '__main__':
    print("Bot started")
    main()
