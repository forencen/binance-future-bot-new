import websockets
import json
from trading_utils.balance import get_available_balance_usdt
from trading_utils.trade import close_open_orders
from telegram_utils import send_telegram_message
from socket_utils.setup import create_listen_key, get_websocket_url

# Function to process incoming WebSocket messages
async def process_order_update(client,data):
    if data['e'] == 'ORDER_TRADE_UPDATE':
        order_update = data['o']
        symbol = order_update['s']
        order_id = order_update['i']
        side = order_update['S']
        status = order_update['X']
        price = order_update['p']
        stopPrice = order_update['sp']
        original_type = order_update['ot']
        pnl = order_update.get('rp', 0)  # Realized PNL
        msg = '',
        availableBalance = 0,
        if original_type == 'LIMIT' or original_type == 'TAKE_PROFIT_MARKET' or original_type == 'STOP_MARKET':
            availableBalance = get_available_balance_usdt(client)
        if status == 'NEW' and original_type == 'LIMIT':
            msg = f'Order ID: {order_id}\nPlaced {side} order {symbol} at {price}\nAvailable Balance: {availableBalance} USDT'
        elif status == 'FILLED':
            if original_type == 'STOP_MARKET':
                msg = f'Order ID: {order_id}\nStop loss {symbol} at {stopPrice}\nPNL: {pnl} USDT\nAvailable Balance: {availableBalance} USDT'
                close_open_orders(client, symbol)
            elif original_type == 'TAKE_PROFIT_MARKET':
                msg = f'Order ID: {order_id}\nTake profit {symbol} at {stopPrice}\nPNL: {pnl} USDT\nAvailable Balance: {availableBalance} USDT'
                close_open_orders(client, symbol)
        if len(msg) > 0: 
            send_telegram_message(msg)
            print(msg)
    
# Function to connect to WebSocket and listen for events
async def listen_for_order_updates(client):
    listen_key = create_listen_key(client)
    if listen_key is None:
        return

    websocket_url = get_websocket_url(listen_key)
    async with websockets.connect(websocket_url) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(data)
                await process_order_update(client,data)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
                break    
