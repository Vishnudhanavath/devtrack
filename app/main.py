from fastapi import FastAPI, HTTPException, status
from app.api.v1.users import router as users_router


app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(users_router,prefix='/api/v1')