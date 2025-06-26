from obsws_python import OBSSocket
import asyncio

async def main():
    async with OBSSocket(host='localhost', port=4460, password=None) as obs:
        version = await obs.call('GetVersion')
        print("Connected! OBS WebSocket Version Info:")
        print(version)

asyncio.run(main())
