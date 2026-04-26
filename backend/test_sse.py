import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sse_starlette import EventSourceResponse

app = FastAPI()

async def test_gen():
    yield "event: progress\r\ndata: {\"foo\":\"bar\"}\r\n\r\n"
    yield {"event": "progress", "data": "{\"foo\":\"baz\"}"}

@app.get("/stream")
async def stream():
    return EventSourceResponse(test_gen())

client = TestClient(app)
response = client.get("/stream")
print(response.content.decode())
