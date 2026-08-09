from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routes import router

app = FastAPI(
    title="Blog Writing Agent API",
    description="LangGraph-powered technical blog generator",
    version="1.0.0",
)

# CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite / CRA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve generated images
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/")
def root():
    return {"message": "Blog Writing Agent API is running"}
