from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def fake_streamer(data: str):
    # Simulate streaming response chunk by chunk
    for word in data.split():
        yield word + " "
        await asyncio.sleep(0.3)

@app.post("/")
async def stream_endpoint(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    # Here you'd use your agent logic to stream responses.
    # We'll simulate with fake_streamer for the example.
    return StreamingResponse(fake_streamer("hello there, how are you too?"), media_type="text/plain")


from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "admin"
    correct_password = "password"
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.post("/protected")
async def protected_route(credentials: HTTPBasicCredentials = Depends(verify_basic_auth)):
    return {"message": "You are authenticated with basic auth!"}

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from paddleocr import PaddleOCR
import base64
import numpy as np
import cv2
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

from functools import lru_cache

@lru_cache(maxsize=1)
def get_ocr():
    return PaddleOCR(
        # use_angle_cls=True, 
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,)

class FileAttachment(BaseModel):
    filename: str
    content_type: str
    data: str  # Base64 encoded

class OCRRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[dict]] = None
    files: Optional[List[FileAttachment]] = None

def ocr_image_to_text(image_bytes: bytes) -> str:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return ""
    img = resize_if_needed(img, max_side=1600)
        # Force dtype uint8
    if img.dtype != np.uint8:
        img = img.astype(np.uint8, copy=False)

    # Force contiguous memory (fixes many bus errors)
    img = np.ascontiguousarray(img)

    result = get_ocr().predict(img)
    if not result:
        return ""
    print(f"result: {result}")
    lines = []
    for res in result:
        j = getattr(res, "json", None)
        if not isinstance(j, dict):
            continue

        texts = j.get("rec_texts") or []
        scores = j.get("rec_scores") or []

        for i, text in enumerate(texts):
            if text and str(text).strip():
                lines.append(str(text).strip())

    return "\n".join(lines)


def build_results_table(results: List[dict]) -> str:
    if not results:
        return "*No files processed*"

    table = "| File | Type | Status | Extracted Text |\n"
    table += "|------|------|--------|----------------|\n"
    for r in results:
        filename = r.get("filename", "unknown")
        file_type = r.get("type", "unknown")
        status = r.get("status", "unknown")
        text = (r.get("text", "") or "").replace("\n", " ").replace("|", "\\|")
        if len(text) > 100:
            text = text[:100] + "..."
        table += f"| {filename} | {file_type} | {status} | {text} |\n"
    return table

def resize_if_needed(img, max_side=1600):
    h, w = img.shape[:2]
    print(f"original image size: {w}x{h}")
    max_current = max(h, w)

    if max_current <= max_side:
        return img

    scale = max_side / max_current
    new_w = int(w * scale)
    new_h = int(h * scale)
    print(f"resizing image from {w}x{h} to {new_w}x{new_h}")
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

@app.post("/ocr-to-markdown")
async def ocr_to_markdown(request: OCRRequest):
    results = []

    user_message = request.message
    if not user_message and request.messages:
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
    if request.files:
        for f in request.files:
            # try:
            data = f.data
            if "," in data:
                data = data.split(",", 1)[1]  # strip data URL prefix if present

            # Log base64 metadata ONLY (safe)
            prefix = data[:30] if data else ""
            print(
                f"[DEBUG] content_type={f.content_type}, "
                f"data_prefix='{prefix}...', "
                f"data_length={len(data) if data else 0}"
            )

            file_bytes = base64.b64decode(data)

            if f.content_type.startswith("image/"):
                extracted = ocr_image_to_text(file_bytes)
                results.append({
                    "filename": f.filename,
                    "type": "image",
                    "status": "✅ Success",
                    "text": extracted if extracted else "(no text detected)"
                })
            else:
                results.append({
                    "filename": f.filename,
                    "type": f.content_type,
                    "status": "❌ Unsupported",
                    "text": f"Cannot process {f.content_type}"
                })

            # except Exception as e:
            #     results.append({
            #         "filename": f.filename,
            #         "type": f.content_type,
            #         "status": "❌ Error",
            #         "text": str(e)
            #     })

    md = []
    if user_message:
        md.append(f"**User Request:** {user_message}\n\n")

    md.append("## OCR Results\n\n")
    md.append(build_results_table(results))
    md.append("\n")

    md.append("\n## Full Extracted Text\n\n")
    for r in results:
        if r["status"].startswith("✅") and r["text"] and r["text"] != "(no text detected)":
            md.append(f"### {r['filename']}\n\n")
            md.append(f"```\n{r['text']}\n```\n\n")

    return StreamingResponse("".join(md), media_type="text/markdown")