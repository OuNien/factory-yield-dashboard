from fastapi import FastAPI

app = FastAPI(title="Factory Yield Dashboard API")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "factory-yield-api"}
