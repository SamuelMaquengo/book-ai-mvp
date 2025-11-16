# backend/app/ai_clients.py
import os, json, base64, requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PLAYGROUND_API_KEY = os.getenv("PLAYGROUND_API_KEY", "")

def build_story_prompt(payload):
    pages = payload.get("pages", 14)
    prompt = f"""
Você é um autor experiente de livros infantis. Gera APENAS um JSON válido com as keys:
{{"title":"<Título>","dedicatoria":"<dedicatoria>","pages":[{{"page":1,"text":"..."}}...]}}
Dados: Nome: {payload['name']}; Idade: {payload['age']}; Idioma: {payload.get('language','pt')}; Tema: {payload['theme']}; Valores: {', '.join(payload.get('values',[]))}; Descrição: {payload.get('description','')}
Regras:
- Gera exatamente {pages} entradas em "pages".
- Cada página: 20-40 palavras, linguagem simples e apropriada.
- Retorna apenas JSON, sem comentários.
"""
    return prompt

def generate_story_with_groq(payload):
    prompt = build_story_prompt(payload)
    if not GROQ_API_KEY:
        # fallback local(dummy) se não tens chave: gera mock simples
        pages = []
        for i in range(payload.get("pages",14)):
            pages.append({"page": i+1, "text": f"{payload['name']} está numa pequena aventura na página {i+1}. Texto de exemplo simples."})
        return {"title": f"A aventura de {payload['name']}", "dedicatoria": f"Para {payload['name']}", "pages": pages}

    url = "https://api.groq.com/v1/outputs"  # ajusta se necessário
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"}
    data = {"model":"llama-3.1","input": prompt, "max_output_tokens": 1200}
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    js = r.json()
    # Extrair texto — pode variar conforme resposta Groq; tenta obter output_text
    text = js.get("output_text") or js.get("data",[{}])[0].get("generated_text","")
    try:
        story = json.loads(text)
    except:
        # fallback simples separar em páginas
        lines = [l.strip() for l in text.split("\n\n") if l.strip()]
        pages = []
        for i in range(payload.get("pages",14)):
            pages.append({"page":i+1,"text": lines[i] if i < len(lines) else f"{payload['name']} está numa pequena aventura."})
        story = {"title": f"A aventura de {payload['name']}", "dedicatoria":"", "pages": pages}
    return story

def generate_image_with_playground(prompt):
    # Se não tens chave, retorna uma imagem placeholder (1x1 transparent png)
    if not PLAYGROUND_API_KEY:
        return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII=")
    url = "https://api.playgroundai.com/v1/images/generate"  # confirmar endpoint
    headers = {"Authorization": f"Bearer {PLAYGROUND_API_KEY}", "Content-Type":"application/json"}
    payload = {"prompt":prompt, "width":1024, "height":1536}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    js = r.json()
    # obter base64 conforme resposta
    img_b64 = js.get("image_base64") or (js.get("data",[{}])[0].get("b64_json"))
    return base64.b64decode(img_b64)
