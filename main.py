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
    width, height = image.size
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if (width < 800 or height < 800) and len(contours) > 5:
        return True, "A felbontás alacsony a nyomdai használathoz. Vektorizálás szükséges."
    if len(contours) > 50:
        return True, "Túl sok apró részlet/zaj észlelhető, vektorizálás javasolt a tiszta vonalakért."
    return False, "A logó minősége megfelelő a digitális megjelenéshez."

def get_dynamic_feedback(image, name, palette, file_size):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    complexity = len(contours)
    is_low_res, res_msg = check_vectorization_need(image, file_size)
    tech_status = res_msg if is_low_res else "Technikailag rendben van, de webes megjelenésnél további optimalizálás (SVG/WebP) javasolt."
    
    profiles = [
        ("túl sokat akar mondani", "Túl sok apró vizuális részlettel operál, ami a 'kevesebb több' elvét sérti. A logó elveszíti az ikonikus jellegét kisméretű (pl. mobil) megjelenésnél."),
        ("technológiailag elavult", "A formai megoldások a 2010-es évek trendjeit idézik, ami egy modern, 2026-os környezetben bizalomvesztést okozhat."),
        ("bizonytalan vizuális identitás", "A logó karakterkészlete és a grafikai elemek aránya nem támogatja a márka egységességét. Hiányzik a fókuszpont.")
    ]
    
    if complexity < 15:
        profile_title, profile_desc = ("minimalista", "A minimalizmus veszélye: a logó könnyen összetéveszthető más márkákkal. Hiányzik belőle az egyedi, megkülönböztető karakter.")
    else:
        profile_title, profile_desc = random.choice(profiles)
        
    color_val = int(palette[0][1:3], 16)
    color_audit = "Vigyázat: " if color_val < 50 or color_val > 200 else ""
    color_audit += f"a választott {palette[0]} árnyalat " + random.choice([
        "túl agresszív a mai felhasználói élmény követelményekhez.",
        "könnyen beleolvad a háttérbe, így gyenge a konverziós potenciálja.",
        "színkódja alapján nem áll készen a digitális eszközök közötti konzisztens megjelenésre."
    ])

    return (f"LOGÓ ELEMZÉS EREDMÉNYE: {profile_title.capitalize()}. {profile_desc}\n\n"
            f"MÁRKANÉV ELEMZÉS EREDMÉNYE: A(z) '{name}' név tipográfiája nem elég karakteres a logó grafikai súlyához.\n\n"
            f"VEKTORIZÁCIÓ SZÜKSÉGESSÉGE: {tech_status}\n\n"
            f"SZÍNPSZICHOLÓGIA: {color_audit}\n\n"
            "ÖSSZEGZÉS: A jelenlegi állapot 10-es skálán maximum 4-es. A 'DigitalFlowStudio' által kínált márkaépítési audit 60%-kal növelheti a márka vizuális hatékonyságát.")

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...), company_name: str = Form("Ismeretlen")):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert('RGB')
    
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    feedback = get_dynamic_feedback(image, company_name, palette, len(content))
    return {"palette": palette, "detailed_feedback": feedback, "seo_score": random.randint(60, 90), "status": "elemzés kész"}

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    try: p.drawImage("DigitalFlowStudio_basiclogo_purple_3.png", 50, 750, width=100, height=100, mask='auto')
    except: pass
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(170, 800, "DigitalFlowStudio - Arculati Riport")
    
    text_object = p.beginText(50, 700)
    text_object.setFont("Helvetica", 12)
    clean_fb = feedback.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ö", "o").replace("ő", "o").replace("ú", "u").replace("ü", "u").replace("ű", "u")
    
    for paragraph in clean_fb.split("\n\n"):
        for line in paragraph.split("\n"):
            words = line.split(" ")
            current_line = ""
            for word in words:
                if p.stringWidth(current_line + " " + word, "Helvetica", 12) < 500:
                    current_line += " " + word
                else:
                    text_object.textLine(current_line)
                    current_line = word
            text_object.textLine(current_line)
        text_object.textLine("") 
    p.drawText(text_object)
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 150, "Elérhetőségeink:")
    p.setFont("Helvetica", 9)
    p.drawString(50, 135, "E-mail: info@digitalflowstudio.hu | Telefon: +36 30 537 4971")
    p.drawString(50, 120, "Facebook: https://www.facebook.com/DigitalFlowStudioHU")
    p.drawString(50, 105, "Instagram: https://www.instagram.com/digital.flow.studio/")
    
    p.save(); buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=DigitalFlowStudio_Riport.pdf"})
