import logging
import random
import io
import cv2
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from reportlab.pdfgen import canvas

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SEO AUDIT MODUL ---
def analyze_website_seo(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "HIÁNYZIK"
        h1 = [h.text for h in soup.find_all('h1')]
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc = meta_desc["content"] if meta_desc else "HIÁNYZIK"
        
        score = 0
        if len(h1) >= 1: score += 40
        if desc != "HIÁNYZIK": score += 30
        if title != "HIÁNYZIK": score += 30
        
        return f"SEO PONTOSZÁM: {score}/100. Cím: {title[:30]}... H1-ek száma: {len(h1)}. Meta leírás: {'OK' if desc != 'HIÁNYZIK' else 'HIÁNYZIK'}."
    except Exception as e:
        return f"SEO Elemzés nem futtatható: {str(e)}"

# --- LOGÓ AUDIT MODUL ---
def check_vectorization_need(image, file_size):
    width, height = image.size
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if (width < 800 or height < 800) and len(contours) > 5:
        return True, "A felbontás alacsony nyomdai használathoz. Vektorizálás szükséges."
    return False, "A minőség digitális használatra megfelelő."

def get_dynamic_feedback(image, name, palette, file_size, url_seo):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    complexity = len(contours)
    _, res_msg = check_vectorization_need(image, file_size)
    
    profile = "Minimalista" if complexity < 15 else "Részletgazdag/Komplex"
    
    return (f"--- SZAKÉRTŐI BRAND & SEO AUDIT ---\n\n"
            f"LOGÓ PROFIL: {profile}. Technikai diagnózis: {res_msg}\n\n"
            f"SEO EREDMÉNYEK: {url_seo}\n\n"
            f"SZÍNPSZICHOLÓGIA: {palette[0]} alapú paletta egy {random.choice(['innovatív', 'bizalmat ébresztő', 'bátor'])} márkát ígér.\n\n"
            "ÖSSZEGZÉS: A diagnózis alapján a márka láthatósága és bizalmi indexe jelentősen növelhető. "
            "A DigitalFlowStudio technikai és grafikai optimalizációval 60%-kal hatékonyabbá teheti a megjelenésedet.")

@app.post("/full-audit")
async def full_audit(url: str = Form(...), file: UploadFile = File(...), company_name: str = Form("Ismeretlen")):
    # 1. SEO elemzés
    seo_results = analyze_website_seo(url)
    
    # 2. Logó feldolgozás
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert('RGB')
    img_array = np.array(image.resize((64, 64))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=5).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    feedback = get_dynamic_feedback(image, company_name, palette, len(content), seo_results)
    return {"palette": palette, "detailed_feedback": feedback}

@app.get("/generate-pdf")
async def generate_pdf(feedback: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 18); p.drawString(50, 800, "DigitalFlowStudio - Profi Audit Riport")
    text = p.beginText(50, 750); text.setFont("Helvetica", 12)
    for line in feedback.split("\n"): text.textLine(line)
    p.drawText(text); p.save(); buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
