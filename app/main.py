from fastapi import FastAPI
from app.api.api import router as api_router

app = FastAPI(title="trashos-api")
app.include_router(api_router, prefix="/api")

@app.get('/') 
def root():
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)