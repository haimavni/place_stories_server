#!/usr/bin/env python

import asyncio
import websockets

async def hello(websocket):
    
    greeting = f"Hello!"

    await websocket.send(greeting)
    print(f">>> {greeting}")

async def main():
    print("started websockets")
    async with websockets.serve(hello, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

print("started ws?")  
asyncio.run(main())  