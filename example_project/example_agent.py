from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def fake_streamer(data: str):
    # Simulate streaming response chunk by chunk
    for word in data.split():
        yield word + " "
        await asyncio.sleep(0.3)

@app.post("/")
async def stream_endpoint(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    # Here you'd use your agent logic to stream responses.
    # We'll simulate with fake_streamer for the example.
    return StreamingResponse(fake_streamer("hello there, how are you too?"), media_type="text/plain")
