from pybit.unified_trading import WebSocket
from time import sleep
from pprint import pprint


def main():
<<<<<<< HEAD
    ws = WebSocket(
        testnet=False,
        channel_type='spot',
    )
=======
    try:
        ws = WebSocket(
            testnet=False,
            channel_type='spot',
            trace_logging=True,
        )
>>>>>>> 5a9bdf6 (changed calculating logic)

        def handle_message(message):
            pprint(message, width=200)

<<<<<<< HEAD
    ws.ticker_stream(
        symbol='APEXUSDT',
        callback=handle_message,
    )
=======
        ws.ticker_stream(
            symbol='BTCUSDT',
            callback=handle_message,
        )
>>>>>>> 5a9bdf6 (changed calculating logic)

        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Bot stopped")


if __name__ == '__main__':
    print("Bot started")
    main()
