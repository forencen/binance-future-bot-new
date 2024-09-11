from keys import api, secret, api_testnet, secret_testnet
from binance.um_futures import UMFutures
import ta
import pandas as pd
from time import sleep
from binance.error import ClientError
from telegram_utils import send_telegram_message
import threading
from pprint import pprint
import websockets
import asyncio
import json
# client = UMFutures(key=api_testnet, secret=secret_testnet, base_url="https://testnet.binancefuture.com")

client = UMFutures(key=api, secret=secret)


# allOrders = client.get_all_orders('DASHUSDT')

# pprint(allOrders)



# def get_tickers_usdt():
#     tickers = []
#     resp = client.ticker_price()
#     for elem in resp:
#         if 'USDT' in elem['symbol']:
#             tickers.append(elem['symbol'])
#     return tickers


# def get_order_history_by_symbol(symbol):
#     allOrders = client.get_all_orders(symbol)
#     return allOrders


# def send_telegram_message_by_symbol(symbol, orders):
#     for elem in orders:
#         symbol = elem['symbol']
#         avgPrice = elem['avgPrice']
#         status = elem['status']
#         if status == 'FILLED':
#             if elem['origType'] == 'STOP_MARKET':
#                 message = f"Stop loss {symbol} at {avgPrice}"
#                 send_telegram_message(message)
#             elif elem['origType'] == 'TAKE_PROFIT_MARKET':
#                 message = f"Take Profit {symbol} at {avgPrice}"
#                 send_telegram_message(message)

# def send_all_take_profit_and_stop_loss_message():
#     tickers = get_tickers_usdt()
#     for symbol in tickers:
#         orders = get_order_history_by_symbol(symbol)
#         send_telegram_message_by_symbol(symbol, orders)


# send_all_take_profit_and_stop_loss_message()



client = UMFutures(api, secret)

# Generate Listen Key for WebSocket User Data Stream
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
        executed_qty = order_update['z']
        pnl = order_update.get('rp', 0)  # Realized PNL
        msg = f"Order Update: Symbol: {symbol}, Order ID: {order_id}, Side: {side}, Status: {status}, Price: {price}, Executed Qty: {executed_qty}, PNL: {pnl}"
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
                await process_order_update(data)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
                break

# Start listening to WebSocket
asyncio.run(listen_for_order_updates())
