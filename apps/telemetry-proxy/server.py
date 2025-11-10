from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

app = FastAPI()

async def event_stream():
    i = 0
    while True:
        payload = {"seq": i, "ts": time.time()}
        yield f"data: {json.dumps(payload)}\n\n"
        i += 1
        await asyncio.sleep(2)

@app.get("/telemetry/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")