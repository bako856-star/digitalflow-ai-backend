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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def analyze_logo_depth(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    count = len(contours)
    if count < 3: return "minimalista és ikonikus", "Kiválóan mutat kisméretű felületeken, mint a közösségi média profilképek."
    elif count < 10: return "kiegyensúlyozott és professzionális", "Ideális egyensúlyt teremt a részletesség és az olvashatóság között."
    else: return "komplex és részletgazdag", "Nagyszerű a történetmesélésre, de nyomdai előkészítésnél figyelj a részletek vesztésére."

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert('RGB')
    
    # Színelemzés - Súlyozottabb
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    # Geometria + Személyre szabott szöveg
    geo_desc, geo_advice = analyze_logo_depth(image)
    
    feedback = (f"Elemzésünk alapján a logód {geo_desc}. "
                f"A domináns {palette[0]} szín mélységet ad a márkádnak. "
                f"{geo_advice} A színpalettád további elemei ({', '.join(palette[1:])}) "
                "lehetőséget adnak a kontrasztos kiemelésekre.")
    
    return {"palette": palette, "detailed_feedback": feedback, "status": "elemzés kész"}

@app.get("/generate-pdf")
async def generate_pdf(feedback: str, palette: str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    # Stílusos fejléc
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, "DigitalFlowStudio - Szakértői Arculati Riport")
    p.setFont("Helvetica", 12)
    # Szöveg tördelése (egyszerű változat)
    y = 750
    for line in [feedback[i:i+80] for i in range(0, len(feedback), 80)]:
        p.drawString(50, y, line)
        y -= 20
    p.drawString(50, y-20, f"Felismert színkódok: {palette}")
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=riport.pdf"})
