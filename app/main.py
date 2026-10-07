from fastapi import FastAPI, HTTPException, status
from app.api.v1.users import router as users_router 
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.project_members import router as project_members_router
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(users_router,prefix='/api/v1')
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router,prefix="/api/v1")
app.include_router(project_members_router,prefix="/api/v1")