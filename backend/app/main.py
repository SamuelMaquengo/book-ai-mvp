# backend/app/main.py
import os
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from ai_clients import generate_story_with_groq, generate_image_with_playground
from pdf_builder import build_pdf_from_story

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Livro IA - MVP")

class BookRequest(BaseModel):
    name: str
    age: int
    language: str = "pt"
    theme: str
    values: list = []
    art_style: str = "cartoon"
    description: str = ""
    pages: int = 14

jobs = {}

@app.post("/generate-book")
async def generate_book(req: BookRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued"}
    background_tasks.add_task(process_book_job, job_id, req.dict())
    return {"job_id": job_id}

@app.get("/job-status/{job_id}")
async def job_status(job_id: str):
    return jobs.get(job_id, {"status":"not_found"})

@app.get("/download/{job_id}")
async def download(job_id: str):
    job_dir = MEDIA_DIR / job_id
    pdfs = list(job_dir.glob("*.pdf")) if job_dir.exists() else []
    if not pdfs:
        return {"error":"not found"}
    # devolve o caminho do ficheiro (local). Para deploy usa URL público (Supabase/Deta)
    return {"path": str(pdfs[0])}

def process_book_job(job_id, payload):
    try:
        jobs[job_id] = {"status":"generating_text"}
        story = generate_story_with_groq(payload)

        job_dir = MEDIA_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        with open(job_dir / "story.json","w",encoding="utf-8") as f:
            json.dump(story, f, ensure_ascii=False, indent=2)

        jobs[job_id] = {"status":"generating_images","progress":0}
        images = []
        # estratégia grátis: gerar poucas imagens (capa + 3 interiores + final)
        pages = payload.get("pages",14)
        pages_to_image = [0] + [max(1, pages//3), max(1, pages//2), pages-1]

        for i, pg_idx in enumerate(pages_to_image):
            jobs[job_id]["progress"] = int((i+1)/len(pages_to_image)*100)
            prompt = f"Ilustração estilo {payload['art_style']} para a página {pg_idx+1}. Criança: {payload['description']}. Tema: {payload['theme']}. Cores vivas, estilo infantil, sem texto."
            img_bytes = generate_image_with_playground(prompt)
            img_path = job_dir / f"page_{pg_idx+1}.png"
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            images.append(str(img_path))

        jobs[job_id] = {"status":"building_pdf"}
        pdf_path = job_dir / f"{payload['name']}_{job_id}.pdf"
        build_pdf_from_story(story, images, pdf_path)
        jobs[job_id] = {"status":"done", "download": str(pdf_path)}
    except Exception as e:
        jobs[job_id] = {"status":"error", "error": str(e)}
