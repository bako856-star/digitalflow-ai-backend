from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io
import cv2
from reportlab.pdfgen import canvas

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def analyze_geometry(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    count = len(contours)
    if count > 15: return "túlzottan komplex", "részletgazdagsága rontja az emlékezetességet és a nyomdai minőséget."
    return "megfelelő", "geometriai kialakítása kellően letisztult."

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...), company_name: str = Form("Ismeretlen")):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert('RGB')
    
    # Színelemzés
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    # Kritikus elemzés
    geo_desc, geo_advice = analyze_geometry(image)
    critique = [f"Logód geometriailag {geo_desc}; {geo_advice}"]
    
    # Név elemzése
    name_len = len(company_name.split())
    if name_len > 3: critique.append("A cégnév túl hosszú, ami megnehezíti a marketingkommunikációt.")
    elif len(company_name) < 3: critique.append("A cégnév túl rövid, bizalmatlanságot szülhet.")
    
    feedback = " ".join(critique) + " Javasoljuk egy professzionális arculati felülvizsgálat elvégzését."
    
    return {
        "palette": palette,
        "detailed_feedback": feedback,
        "seo_score": 75, # Alapértelmezett, tesztelhető
        "status": "elemzés kész"
    }

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    try:
        p.drawImage("DigitalFlowStudio_basiclogo_purple_3.png", 400, 750, width=150, height=50, mask='auto')
    except: pass
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, "DigitalFlowStudio - Kritikus Arculati Riport")
    p.setFont("Helvetica", 12)
    y = 750
    clean_fb = feedback.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ő", "o").replace("ú", "u").replace("ü", "u").replace("ű", "u")
    for line in [clean_fb[i:i+80] for i in range(0, len(clean_fb), 80)]:
        p.drawString(50, y, line); y -= 20
    p.drawString(50, y-20, f"Szinek: {palette}")
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=riport.pdf"})
