from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io
import cv2
from reportlab.pdfgen import canvas

app = FastAPI()

# CORS beállítás a WordPress kommunikációhoz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_geometry(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return "komplex, részletgazdag" if len(contours) > 5 else "minimalista, letisztult"

def analyze_style(palette, geo_type):
    return (f"A logód egy {geo_type} stílusú alkotás. "
            f"Az észlelt {palette[0]} színvilág modern és figyelemfelkeltő. "
            "Ajánlásunk: A márkaidentitásod erősítése érdekében ügyelj a kontrasztra a webes felületeken.")

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert('RGB')
    
    # Színelemzés
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    # Geometria
    geo_type = analyze_geometry(image)
    feedback = analyze_style(palette, geo_type)
    
    return {
        "palette": palette,
        "detailed_feedback": feedback,
        "status": "elemzés kész"
    }

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "DigitalFlowStudio - Arculati Riport")
    p.drawString(100, 780, f"Elemzés: {feedback}")
    p.drawString(100, 760, f"Színek: {palette}")
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=riport.pdf"})
