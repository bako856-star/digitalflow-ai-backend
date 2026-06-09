from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io

app = FastAPI()

# Engedélyezzük a kapcsolatot a WordPress oldaladról
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://digitalflowstudio.hu"], # Élesben itt a domain-edet érdemes megadni
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_dominant_colors(image, k=3):
    image = image.resize((100, 100))
    img_array = np.array(image).reshape(-1, 3)
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(img_array)
    colors = kmeans.cluster_centers_.astype(int)
    return ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in colors]
def analyze_style(palette):
    # Egyszerű elemző logika
    analysis = []
    if len(palette) >= 2:
        # Példa logikára: kontraszt elemzés vagy stílus kategória
        analysis.append("A logód dinamikus, mivel kontrasztos színeket tartalmaz.")
    
    analysis.append("Stílusjavaslat: Minimalista, modern vállalati megjelenés ajánlott.")
    return " ".join(analysis)

@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert('RGB')
    palette = get_dominant_colors(image)
    
    # Új: Részletes szöveges elemzés generálása
    feedback = analyze_style(palette)
    
    return {
        "palette": palette,
        "detailed_feedback": feedback,  # Ezt küldjük vissza
        "status": "elemzés kész"
    }
@app.post("/analyze-logo")
async def analyze_logo(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert('RGB')
    palette = get_dominant_colors(image)
    return {"palette": palette, "status": "elemzés kész"}
