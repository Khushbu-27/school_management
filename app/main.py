
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from requests import post
from app.blueprints.routers import router


app = FastAPI(title="School mangement API", version="1.0")

# Include centralized router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
