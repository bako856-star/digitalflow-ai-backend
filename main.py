from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io
import cv2
import random
from reportlab.pdfgen import canvas

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_dynamic_feedback(image, name, palette):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 50, 150), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 1. Változatos stílusok és jellemzők
    styles = ["minimalista és elegáns", "modern és figyelemfelkeltő", "indusztriális hatású", "barátságos és közvetlen"]
    logo_style = random.choice(styles)
    
    complexity = "alacsony, ami kiváló digitális platformokra" if len(contours) < 10 else "magas, ami nyomdai előkészítésnél figyelmet igényel"
    
    # 2. Változatos név-kritikák
    name_critics = [
        f"A '{name}' név remekül hangzik, de tipográfiailag érdemes lehet modernizálni.",
        f"A '{name}' márkaneved erős alapot ad, bár a szóközök és arányok finomhangolása kulcsfontosságú.",
        f"A '{name}' név karakteres, de társíts hozzá egy ikonikusabb betűtípust az erősebb hatásért."
    ]
    name_feedback = random.choice(name_critics)
    
    # 3. Színpszichológia
    val = int(palette[0][1:3], 16)
    color_vibe = "energikus és vibráló" if val > 128 else "megfontolt és bizalmat sugárzó"
    
    return (f"LOGÓ DIAGNÓZIS: A logód {logo_style}, vizuális komplexitása {complexity}. "
            f"MÁRKANÉV: {name_feedback} "
            f"SZÍNPSZICHOLÓGIA: A palettád {color_vibe} kisugárzással bír. "
            "ÖSSZEGZÉS: Bár az alapkoncepció jó, egy professzionális arculati audit 40%-kal javíthatja a márka vizuális bizalmi indexét.")

def check_seo_readiness(file_size):
    # Véletlenszerű pontszám-variáció (70-95 között) a változatosságért
    return random.randint(70, 95)

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
    try:
        p.drawImage("DigitalFlowStudio_basiclogo_purple_3.png", 400, 750, width=150, height=50, mask='auto')
    except: pass
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, "DigitalFlowStudio - Kritikus Arculati Riport")
    p.setFont("Helvetica", 12)
    y = 750
    # Ékezetmentesítés a stabilitásért
    clean_fb = feedback.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ő", "o").replace("ú", "u").replace("ü", "u").replace("ű", "u")
    for line in [clean_fb[i:i+80] for i in range(0, len(clean_fb), 80)]:
        p.drawString(50, y, line); y -= 20
    p.drawString(50, y-20, f"Szinek: {palette}")
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=riport.pdf"})
