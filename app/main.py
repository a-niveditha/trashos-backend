from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import router as api_router

app = FastAPI(title="trashos-api")

# cors will be the end of me
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # CHANGE IN PROD!!  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get('/') 
def root():
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)