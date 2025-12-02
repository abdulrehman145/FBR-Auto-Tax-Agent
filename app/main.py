from fastapi import FastAPI
from app.routes.documents import router as documents_router
from app.routes.runs import router as runs_router
from app.routes.admin import router as admin_router
from app.routes.webhooks import router as webhook_router

app = FastAPI()

app.include_router(documents_router)
app.include_router(runs_router)
app.include_router(admin_router)
app.include_router(webhook_router)

@app.get("/healthz")
async def health():
    return {"ok": True}
