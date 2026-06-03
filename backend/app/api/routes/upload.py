from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Optional raw binary file upload router.
    """
    return {"filename": file.filename, "content_type": file.content_type, "status": "uploaded"}
