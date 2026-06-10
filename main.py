from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io
import cv2 # Új könyvtár

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_geometry(image):
    # Kép konvertálása OpenCV formátumba
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Élek keresése (Canny edge detection)
    edges = cv2.Canny(gray, 50, 150)
    # Kontúrok számlálása
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 5:
        return "komplex, részletgazdag"
    else:
        return "minimalista, letisztult"

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert('RGB')
    
    # Színelemzés
    img_array = np.array(image.resize((100, 100))).reshape(-1, 3)
    kmeans = KMeans(n_clusters=3, n_init=10).fit(img_array)
    palette = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in kmeans.cluster_centers_.astype(int)]
    
    # Geometriai elemzés
    geo_type = analyze_geometry(image)
    
    feedback = f"A logód egy {geo_type} stílusú alkotás. A használt {palette[0]} színvilág modern megjelenést kölcsönöz neki."
    
    return {
        "palette": palette,
        "detailed_feedback": feedback,
        "status": "elemzés kész"
    }
