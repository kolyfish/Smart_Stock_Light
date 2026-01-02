import asyncio
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration
from core.config import SharedConfig

async def test():
    config_obj = SharedConfig()
    username = config_obj.tapo_email
    password = config_obj.tapo_password
    ip = config_obj.tapo_ip
    
    if not username or not password or not ip:
        print("Missing config")
        return

    credentials = AuthCredential(username, password)
    config = DeviceConnectConfiguration(
        host=ip,
        credentials=credentials,
        device_type="SMART.TAPOBULB"
    )
    
    device = await connect(config)
    print(f"Device type: {type(device)}")
    print(f"Attributes: {[attr for attr in dir(device) if not attr.startswith('_')]}")
    if hasattr(device, 'client'):
        print(f"Client attributes: {[attr for attr in dir(device.client) if not attr.startswith('_')]}")
    
    # Try to find close-like method
    for method in ['close', 'disconnect', 'logout', 'stop', 'quit']:
        if hasattr(device, method):
            print(f"Device has {method}")
        if hasattr(device, 'client') and hasattr(device.client, method):
            print(f"Client has {method}")

if __name__ == "__main__":
    asyncio.run(test())
