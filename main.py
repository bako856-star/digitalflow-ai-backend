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

def get_dynamic_feedback(image, name, palette):
    # Geometria elemzés
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 50, 150), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Logó állapot leírása
    count = len(contours)
    if count < 5: logo_msg = "letisztult, modern és könnyen skálázható"
    elif count < 20: logo_msg = "kiegyensúlyozott, professzionális hatású"
    else: logo_msg = "túlzottan komplex, ami rontja a digitális megjelenítést és az emlékezetességet"
    
    # Név elemzés
    name_len = len(name)
    if name_len < 5: name_msg = "rövid és ütős, remekül megjegyezhető"
    elif name_len > 15: name_msg = "hosszú, ami kihívást jelenthet a tipográfiában"
    else: name_msg = "kiegyensúlyozott, jól illeszkedik a modern márkák közé"
    
    # Szín elemzés
    val = int(palette[0][1:3], 16)
    color_msg = "erőt és dinamizmust sugároz" if val > 128 else "visszafogott, bizalmat ébresztő"
    
    return (f"LOGÓ: A logód {logo_msg}. NÉV: A '{name}' márkaneved {name_msg}. "
            f"SZÍNEK: A domináns {palette[0]} szín {color_msg}. "
            "ÖSSZEGZÉS: Bár a márka alapjai megvannak, egy professzionális finomhangolás, "
            "az arculati egység megteremtése és a technikai optimalizálás 30-40%-kal növelheti a hatékonyságodat.")

def check_seo_readiness(file_size):
    score = 100
    if file_size > 500000: score -= 30
    return score

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...), company_name: str = Form("Ismeretlen")):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert('RGB')
    
    # Színelemzés
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    # Elemzések
    feedback = get_dynamic_feedback(image, company_name, palette)
    seo_score = check_seo_readiness(len(content))
    
    return {"palette": palette, "detailed_feedback": feedback, "seo_score": seo_score, "status": "elemzés kész"}

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # Logó beillesztése (ha létezik a fájl)
    try:
        p.drawImage("DigitalFlowStudio_basiclogo_purple_3.png", 400, 750, width=150, height=150, mask='auto')
    except: pass
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, "DigitalFlowStudio - Kritikus Arculati Riport")
    p.setFont("Helvetica", 12)
    y = 750
    # Ékezetmentesítés a PDF stabilitásért
    clean_fb = feedback.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ő", "o").replace("ú", "u").replace("ü", "u").replace("ű", "u")
    for line in [clean_fb[i:i+80] for i in range(0, len(clean_fb), 80)]:
        p.drawString(50, y, line); y -= 20
    p.drawString(50, y-20, f"Felismert szinkodok: {palette}")
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=riport.pdf"})
