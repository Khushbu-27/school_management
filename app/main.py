
from fastapi import FastAPI
from app.blueprints.routers import router


app = FastAPI(title="School mangement API", version="1.0")

# Include centralized router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
