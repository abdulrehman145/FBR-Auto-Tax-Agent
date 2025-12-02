import uuid
from fastapi import APIRouter, UploadFile
from app.services.stores import DOCS

router = APIRouter(prefix="/documents")

@router.post("")
async def upload_doc(f: UploadFile):
    data = await f.read()
    doc_id = str(uuid.uuid4())
    DOCS[doc_id] = data.decode()
    return {"doc_id": doc_id}
