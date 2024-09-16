from keys import api, secret, api_testnet, secret_testnet
from binance.um_futures import UMFutures
from time import sleep
import asyncio
import threading
from trading_utils.balance import get_balance_usdt
from trading_utils.market import get_tickers_usdt
from trading_utils.trade import set_leverage, set_mode, open_order, get_pos, check_orders, close_open_orders
from trading_utils.signal import str_signal, rsi_signal, macd_ema, ema200_50, ema34_89
from socket_utils.orderListener import listen_for_order_updates

# client = UMFutures(key=api_testnet, secret=secret_testnet, base_url="https://testnet.binancefuture.com")

client = UMFutures(key=api, secret=secret)

# 0.012 means +1.2%, 0.009 is -0.9% 
tp = 0.012
sl = 0.009
volume = 10  # volume for one order (if its 10 and leverage is 10, then you put 1 usdt to one position)
leverage = 10
type = 'ISOLATED'  # type is 'ISOLATED' or 'CROSS'
qty = 1  # Amount of concurrent opened positions


# asyncio.run(listen_for_order_updates())
def run_event_loop():
    asyncio.run(listen_for_order_updates(client))
    
symbol = ''
# getting all symbols from Binance Futures list:
symbols = get_tickers_usdt(client)

if __name__ == "__main__":
    thread = threading.Thread(target=run_event_loop)
    thread.start()
    while True:
        # we need to get balance to check if the connection is good, or you have all the needed permissions
        balance = get_balance_usdt(client)
        sleep(1)
        if balance == None:
            print('Cant connect to API. Check IP, restrictions or wait some time')
        if balance != None:
            print("My balance is: ", balance, " USDT")
            # getting position list:
            pos = []
            pos = get_pos(client)
            print(f'You have {len(pos)} opened positions:\n{pos}')
            # Getting order list
            ord = []
            ord = check_orders(client)
            # removing stop orders for closed positions
            for elem in ord:
                if not elem in pos:
                    close_open_orders(client, elem)

            if len(pos) < qty:
                for elem in symbols:
                    # Strategies (you can make your own with the TA library):
                    signal = ema34_89(client, elem, '15m')
                    # 'up' or 'down' signal, we place orders for symbols that arent in the opened positions and orders
                    # we also dont need USDTUSDC because its 1:1 (dont need to spend money for the commission)
                    if signal == 'up' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                        print('Found BUY signal for ', elem)
                        set_mode(client, elem, type)
                        sleep(1)
                        set_leverage(client,elem, leverage)
                        sleep(1)
                        print('Placing order for ', elem)
                        open_order(client, elem, 'buy', volume, tp, sl)
                        symbol = elem
                        order = True
                        pos = get_pos(client)
                        sleep(1)
                        ord = check_orders(client)
                        sleep(1)
                        sleep(10)
                        # break
                    if signal == 'down' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                        print('Found SELL signal for ', elem)
                        set_mode(client, elem, type)
                        sleep(1)
                        set_leverage(client, elem, leverage)
                        sleep(1)
                        print('Placing order for ', elem)
                        open_order(client, elem, 'sell', volume, tp, sl)
                        symbol = elem
                        order = True
                        pos = get_pos(client)
                        sleep(1)
                        ord = check_orders(client)
                        sleep(1)
                        sleep(10)
                        # break
        print('Waiting 3 min')
        sleep(180)
