from keys import api, secret, api_testnet, secret_testnet
from binance.um_futures import UMFutures
import ta
import pandas as pd
from time import sleep
from binance.error import ClientError
from telegram_utils import send_telegram_message
import websockets
import json
import asyncio
import threading

# client = UMFutures(key=api_testnet, secret=secret_testnet, base_url="https://testnet.binancefuture.com")

client = UMFutures(key=api, secret=secret)

# 0.012 means +1.2%, 0.009 is -0.9% 
tp = 0.012
sl = 0.009
volume = 10  # volume for one order (if its 10 and leverage is 10, then you put 1 usdt to one position)
leverage = 10
type = 'ISOLATED'  # type is 'ISOLATED' or 'CROSS'
qty = 1  # Amount of concurrent opened positions



# getting your futures balance in USDT
def get_balance_usdt():
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])

    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
def get_available_balance_usdt():
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['availableBalance'])

    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Getting all available symbols on the Futures ('BTCUSDT', 'ETHUSDT', ....)
def get_tickers_usdt():
    tickers = []
    resp = client.ticker_price()
    for elem in resp:
        if 'USDT' in elem['symbol']:
            tickers.append(elem['symbol'])
    return tickers


# Getting candles for the needed symbol, its a dataframe with 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'
def klines(symbol):
    try:
        resp = pd.DataFrame(client.klines(symbol, '15m'))
        resp = resp.iloc[:,:6]
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        resp = resp.set_index('Time')
        resp.index = pd.to_datetime(resp.index, unit = 'ms')
        resp = resp.astype(float)
        return resp
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Set leverage for the needed symbol. You need this bcz different symbols can have different leverage
def set_leverage(symbol, level):
    try:
        response = client.change_leverage(
            symbol=symbol, leverage=level, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# The same for the margin type
def set_mode(symbol, type):
    try:
        response = client.change_margin_type(
            symbol=symbol, marginType=type, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Price precision. BTC has 1, XRP has 4
def get_price_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['pricePrecision']


# Amount precision. BTC has 3, XRP has 1
def get_qty_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['quantityPrecision']


# Open new order with the last price, and set TP and SL:
def open_order(symbol, side):
    price = float(client.ticker_price(symbol)['price'])
    qty_precision = get_qty_precision(symbol)
    price_precision = get_price_precision(symbol)
    qty = round(volume/price, qty_precision)
    if side == 'buy':
        try:
            resp1 = client.new_order(symbol=symbol, side='BUY', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            # print log
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price - price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price + price * tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                     stopPrice=tp_price)
            print(resp3)
            # Send telegram message
            # order_id = resp1['orderId']
            # balance = get_balance_usdt()
            # availableBalance = get_available_balance_usdt()
            # message = f"Order ID: {order_id}\nPlaced {side} order {symbol} at {price}\nTP/SL:{tp_price}/{sl_price}\nCurrent balance: {balance} USDT\nAvailable balance: {availableBalance} USDT"
            # send_telegram_message(message)
        except ClientError as error:
            error_message = f"Error placing order for {symbol}: {error.error_message}"
            send_telegram_message(error_message)
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
    if side == 'sell':
        try:
            resp1 = client.new_order(symbol=symbol, side='SELL', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price + price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price - price * tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                     stopPrice=tp_price)
            print(resp3)
            # Send telegram message
            # order_id = resp1['orderId']
            # balance = get_balance_usdt()
            # availableBalance = get_available_balance_usdt()
            # message = f"Order ID: {order_id}\nPlaced {side} order {symbol} at {price}\nTP/SL:{tp_price}/{sl_price}\nCurrent balance: {balance} USDT\nAvailable balance: {availableBalance} USDT"
            # send_telegram_message(message)
        except ClientError as error:
            error_message = f"Error placing order for {symbol}: {error.error_message}"
            send_telegram_message(error_message)
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )


# Your current positions (returns the symbols list):
def get_pos():
    try:
        resp = client.get_position_risk()
        pos = []
        for elem in resp:
            if float(elem['positionAmt']) != 0:
                pos.append(elem['symbol'])
        return pos
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def check_orders():
    try:
        response = client.get_orders(recvWindow=6000)
        sym = []
        for elem in response:
            sym.append(elem['symbol'])
        return sym
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

# Close open orders for the needed symbol. If one stop order is executed and another one is still there
def close_open_orders(symbol):
    try:
        response = client.cancel_open_orders(symbol=symbol, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Strategy. Can use any other:
def str_signal(symbol):
    kl = klines(symbol)
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    rsi_k = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_k()
    rsi_d = ta.momentum.StochRSIIndicator(kl.Close).stochrsi_d()
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if rsi.iloc[-1] < 40 and ema.iloc[-1] < kl.Close.iloc[-1] and rsi_k.iloc[-1] < 20 and rsi_k.iloc[-3] < rsi_d.iloc[-3] and rsi_k.iloc[-2] < rsi_d.iloc[-2] and rsi_k.iloc[-1] > rsi_d.iloc[-1]:
        return 'up'
    if rsi.iloc[-1] > 60 and ema.iloc[-1] > kl.Close.iloc[-1] and rsi_k.iloc[-1] > 80 and rsi_k.iloc[-3] > rsi_d.iloc[-3] and rsi_k.iloc[-2] > rsi_d.iloc[-2] and rsi_k.iloc[-1] < rsi_d.iloc[-1]:
        return 'down'
    else:
        return 'none'


def rsi_signal(symbol):
    kl = klines(symbol)
    rsi = ta.momentum.RSIIndicator(kl.Close).rsi()
    if rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30:
        return 'up'
    if rsi.iloc[-2] > 70 and rsi.iloc[-1] < 70:
        return 'down'
    else:
        return 'none'

def macd_ema(symbol):
    kl = klines(symbol)
    macd = ta.trend.macd_diff(kl.Close)
    ema = ta.trend.ema_indicator(kl.Close, window=200)
    if macd.iloc[-3] < 0 and macd.iloc[-2] < 0 and macd.iloc[-1] > 0 and ema.iloc[-1] < kl.Close.iloc[-1]:
        return 'up'
    if macd.iloc[-3] > 0 and macd.iloc[-2] > 0 and macd.iloc[-1] < 0 and ema.iloc[-1] > kl.Close.iloc[-1]:
        return 'down'
    else:
        return 'none'


def ema200_50(symbol):
    kl = klines(symbol)
    ema200 = ta.trend.ema_indicator(kl.Close, window=100)
    ema50 = ta.trend.ema_indicator(kl.Close, window=50)
    if ema50.iloc[-3] < ema200.iloc[-3] and ema50.iloc[-2] < ema200.iloc[-2] and ema50.iloc[-1] > ema200.iloc[-1]:
        return 'up'
    if ema50.iloc[-3] > ema200.iloc[-3] and ema50.iloc[-2] > ema200.iloc[-2] and ema50.iloc[-1] < ema200.iloc[-1]:
        return 'down'
    else:
        return 'none'

def ema34_89(symbol):
    kl = klines(symbol)
    ema89 = ta.trend.ema_indicator(kl.Close, window=89)
    ema34 = ta.trend.ema_indicator(kl.Close, window=34)
    if ema34.iloc[-3] < ema89.iloc[-3] and ema34.iloc[-2] < ema89.iloc[-2] and ema34.iloc[-1] > ema89.iloc[-1]:
        return 'up'
    if ema34.iloc[-3] > ema89.iloc[-3] and ema34.iloc[-2] > ema89.iloc[-2] and ema34.iloc[-1] < ema89.iloc[-1]:
        return 'down'
    else:
        return 'none'

# Create websocket to watch orders  
def create_listen_key():
    try:
        response = client.new_listen_key()
        return response['listenKey']
    except ClientError as error:
        print(f"Error creating listen key: {error}")
        return None

# WebSocket URL
def get_websocket_url(listen_key):
    return f"wss://fstream.binance.com/ws/{listen_key}"

# Function to process incoming WebSocket messages
async def process_order_update(data):
    if data['e'] == 'ORDER_TRADE_UPDATE':
        order_update = data['o']
        symbol = order_update['s']
        order_id = order_update['i']
        side = order_update['S']
        status = order_update['X']
        price = order_update['p']
        stopPrice = order_update['sp']
        executed_qty = order_update['z']
        original_type = order_update['ot']
        pnl = order_update.get('rp', 0)  # Realized PNL
        # msg = f"Order Update: Symbol: {symbol}, Order ID: {order_id}, Side: {side}, Status: {status}, Price: {price}, Executed Qty: {executed_qty}, PNL: {pnl}"
        msg = '',
        availableBalance = 0,
        if original_type == 'LIMIT' or original_type == 'TAKE_PROFIT_MARKET' or original_type == 'STOP_MARKET':
            availableBalance = get_available_balance_usdt()
        if status == 'NEW' and original_type == 'LIMIT':
            msg = f'Order ID: {order_id}\nPlaced {side} order {symbol} at {price}\nAvailable Balance: {availableBalance} USDT'
        if status == 'FILLED':
            if original_type == 'STOP_MARKET':
                msg = f'Order ID: {order_id}\nStop loss {symbol} at {stopPrice}\nPNL: {pnl} USDT\nAvailable Balance: {availableBalance} USDT'
            elif original_type == 'TAKE_PROFIT_MARKET':
                msg = f'Order ID: {order_id}\nTake profit {symbol} at {stopPrice}\nPNL: {pnl} USDT\nAvailable Balance: {availableBalance} USDT'
        send_telegram_message(msg)
        print(msg)

# Function to connect to WebSocket and listen for events
async def listen_for_order_updates():
    listen_key = create_listen_key()
    if listen_key is None:
        return

    websocket_url = get_websocket_url(listen_key)
    async with websockets.connect(websocket_url) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(data)
                await process_order_update(data)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
                break    
# asyncio.run(listen_for_order_updates())
def run_event_loop():
    asyncio.run(listen_for_order_updates())

orders = 0
symbol = ''
# getting all symbols from Binance Futures list:
symbols = get_tickers_usdt()
if __name__ == "__main__":
    thread = threading.Thread(target=run_event_loop)
    thread.start()
    while True:
        # we need to get balance to check if the connection is good, or you have all the needed permissions
        balance = get_balance_usdt()
        sleep(1)
        if balance == None:
            print('Cant connect to API. Check IP, restrictions or wait some time')
        if balance != None:
            print("My balance is: ", balance, " USDT")
            # getting position list:
            pos = []
            pos = get_pos()
            print(f'You have {len(pos)} opened positions:\n{pos}')
            # Getting order list
            ord = []
            ord = check_orders()
            # removing stop orders for closed positions
            for elem in ord:
                if not elem in pos:
                    close_open_orders(elem)

            if len(pos) < qty:
                for elem in symbols:
                    # Strategies (you can make your own with the TA library):

                    # signal = str_signal(elem)
                    # signal = rsi_signal(elem)
                    # signal = macd_ema(elem)
                    signal = ema34_89(elem)

                    # 'up' or 'down' signal, we place orders for symbols that arent in the opened positions and orders
                    # we also dont need USDTUSDC because its 1:1 (dont need to spend money for the commission)
                    if signal == 'up' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                        print('Found BUY signal for ', elem)
                        set_mode(elem, type)
                        sleep(1)
                        set_leverage(elem, leverage)
                        sleep(1)
                        print('Placing order for ', elem)
                        open_order(elem, 'buy')
                        symbol = elem
                        order = True
                        pos = get_pos()
                        sleep(1)
                        ord = check_orders()
                        sleep(1)
                        sleep(10)
                        # break
                    if signal == 'down' and elem != 'USDCUSDT' and not elem in pos and not elem in ord and elem != symbol:
                        print('Found SELL signal for ', elem)
                        set_mode(elem, type)
                        sleep(1)
                        set_leverage(elem, leverage)
                        sleep(1)
                        print('Placing order for ', elem)
                        open_order(elem, 'sell')
                        symbol = elem
                        order = True
                        pos = get_pos()
                        sleep(1)
                        ord = check_orders()
                        sleep(1)
                        sleep(10)
                        # break
        print('Waiting 3 min')
        sleep(180)
