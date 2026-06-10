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

def check_vectorization_need(image, file_size):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 50, 150), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if file_size < 100000 and len(contours) > 10:
        return True, "A logó felbontása alacsony, részletei pixelesedhetnek. Professzionális vektorizálás javasolt!"
    return False, "A logó minősége megfelelő a digitális megjelenéshez."

def get_dynamic_feedback(image, name, palette, file_size):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 50, 150), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    _, res_msg = check_vectorization_need(image, file_size)
    styles = ["minimalista és elegáns", "modern és figyelemfelkeltő", "indusztriális hatású", "barátságos és közvetlen"]
    logo_style = random.choice(styles)
    
    name_critics = [
        f"A '{name}' név remekül hangzik, de tipográfiailag érdemes lehet modernizálni.",
        f"A '{name}' márkaneved erős alapot ad, bár az arányok finomhangolása kulcsfontosságú.",
        f"A '{name}' név karakteres, de társíts hozzá egy ikonikusabb betűtípust az erősebb hatásért."
    ]
    name_feedback = random.choice(name_critics)
    
    val = int(palette[0][1:3], 16)
    color_vibe = "energikus és vibráló" if val > 128 else "megfontolt és bizalmat sugárzó"
    
    return (f"DIAGNÓZIS: A logód {logo_style}, vizuális komplexitása {len(contours)} kontúr. "
            f"MINŐSÉG: {res_msg} "
            f"MÁRKANÉV: {name_feedback} "
            f"SZÍN: A palettád {color_vibe} kisugárzással bír. "
            "ÖSSZEGZÉS: Egy professzionális arculati audit 40%-kal javíthatja a márka vizuális bizalmi indexét.")

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...), company_name: str = Form("Ismeretlen")):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert('RGB')
    
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    feedback = get_dynamic_feedback(image, company_name, palette, len(content))
    return {"palette": palette, "detailed_feedback": feedback, "seo_score": random.randint(70, 95), "status": "elemzés kész"}

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    try: p.drawImage("DigitalFlowStudio_basiclogo_purple_3.png", 50, 750, width=100, height=100, mask='auto')
    except: pass
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(170, 800, "DigitalFlowStudio - Arculati Riport")
    
    p.setFont("Helvetica", 12)
    text_object = p.beginText(50, 700)
    text_object.setFont("Helvetica", 12)
    
    clean_fb = feedback.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ő", "o").replace("ú", "u").replace("ü", "u").replace("ű", "u")
    
    # Tördelt szöveg kezelés
    words = clean_fb.split(" ")
    current_line = ""
    for word in words:
        if p.stringWidth(current_line + " " + word, "Helvetica", 12) < 500:
            current_line += " " + word
        else:
            text_object.textLine(current_line)
            current_line = word
    text_object.textLine(current_line)
    p.drawText(text_object)
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 150, "Elérhetőségeink:")
    p.setFont("Helvetica", 9)
    p.drawString(50, 135, "E-mail: info@digitalflowstudio.hu | Telefon: +36 30 537 4971")
    p.drawString(50, 120, "Facebook: https://www.facebook.com/DigitalFlowStudioHU")
    p.drawString(50, 105, "Instagram: https://www.instagram.com/digital.flow.studio/")
    
    p.save(); buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=DigitalFlowStudio_Riport.pdf"})
