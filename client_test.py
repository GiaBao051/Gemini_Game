import asyncio, json, websockets, sys

URI = "ws://127.0.0.1:8080/ws"

async def main(name: str):
    async with websockets.connect(URI) as ws:
        await ws.send(json.dumps({"type":"join","name":name}))

        async def reader():
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                t = data.get("type")
                if t == "state":
                    # chỉ in tóm tắt
                    players = data.get("players", {})
                    phase = data.get("phase")
                    carrier = data.get("carrier")
                    print(f"[{name}] phase={phase} carrier={carrier} players="
                          f"{ {k:v.get('pos') for k,v in players.items()} }")
                else:
                    print(f"[{name}] << {data}")

        async def writer():
            mapping = {"w":"U","s":"D","a":"L","d":"R"}
            while True:
                key = await asyncio.to_thread(input, f"[{name}] move (w/a/s/d): ")
                key = key.strip().lower()
                if key in mapping:
                    await ws.send(json.dumps({"type":"input","dir":mapping[key]}))

        await asyncio.gather(reader(), writer())

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "P"
    asyncio.run(main(name))
