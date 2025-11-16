# backend/app/pdf_builder.py
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES)))

def build_pdf_from_story(story, images, output_path):
    title = story.get("title","Livro")
    pages = story.get("pages", [])
    # Mapa simples imagens -> páginas (capa + alguns interiores)
    image_map = {}
    if images:
        image_map["cover"] = images[0]
        for i, img in enumerate(images[1:], start=1):
            # map interior images to pages spread
            idx = min(len(pages), i*2)
            image_map[idx] = img

    html = env.get_template("book.html").render(title=title, dedicatoria=story.get("dedicatoria",""), pages=pages, image_map=image_map)
    HTML(string=html, base_url=str(TEMPLATES)).write_pdf(str(output_path))
