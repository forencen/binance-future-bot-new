from binance.error import ClientError
import asyncio

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


# Function to keep the listen key alive every 30 minutes
async def keep_listen_key_alive(client, listen_key):
    while True:
        try:
            client.renew_listen_key(listen_key)  # PUT /fapi/v1/listenKey
            print(f"Listen key {listen_key} extended")
        except ClientError as error:
            print(f"Error keeping listen key alive: {error}")
            if error.code == -1125:  # Listen key does not exist
                print("Listen key expired. Recreating a new one...")
                return False
        await asyncio.sleep(1800)  # Sleep for 30 minutes