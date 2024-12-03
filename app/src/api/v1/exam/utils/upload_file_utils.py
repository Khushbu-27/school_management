
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")