from binance.error import ClientError

# Create websocket to watch orders  
def create_listen_key(client):
    try:
        response = client.new_listen_key()
        return response['listenKey']
    except ClientError as error:
        print(f"Error creating listen key: {error}")
        return None

# WebSocket URL
def get_websocket_url(listen_key):
    return f"wss://fstream.binance.com/ws/{listen_key}"