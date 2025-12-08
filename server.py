import os
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get('/', response_class=PlainTextResponse)
async def root():
    return 'mad-professor: service is running'

def get_port() -> int:
    try:
        return int(os.getenv('PORT', '8000'))
    except ValueError:
        return 8000
