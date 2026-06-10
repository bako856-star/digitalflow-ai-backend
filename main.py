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
    # Színkódok HEX-ből RGB-vé alakítása a számításhoz
    def hex_to_rgb(hex):
        hex = hex.lstrip('#')
        return [int(hex[i:i+2], 16) for i in (0, 2, 4)]

    rgb_colors = [hex_to_rgb(c) for c in palette]
    
    # 1. Értékelés: Színvilág hangulata
    avg_red = sum(c[0] for c in rgb_colors) / len(rgb_colors)
    if avg_red > 150:
        mood = "energikus, szenvedélyes"
    else:
        mood = "nyugodt, bizalomgerjesztő"
        
    # 2. Értékelés: Kontraszt/Változatosság
    if len(set(palette)) < 2:
        complexity = "minimalista"
    else:
        complexity = "sokszínű és figyelemfelkeltő"

    return (f"A logód a {mood} hangulatot sugározza. "
            f"Az általunk észlelt {complexity} színvilág kiválóan alkalmas "
            "a márka első benyomásának megalapozására. "
            "Tipp: Ügyelj arra, hogy a weboldalad háttérszíne ne nyomja el ezeket a tónusokat!")

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
