from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from typing import List

from backend.models import Deck, DeckCreate, Card, Material, GenerateRequest, ExplainRequest
from backend.storage import load_decks, save_decks, load_materials, save_materials
from backend.rag import extract_text_from_file, chunk_text
from backend.ai_service import generate_ai_deck, generate_ai_explanation, generate_mindmap

app = FastAPI(title="EduCards API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/decks", response_model=List[Deck])
def get_decks():
    return load_decks()

@app.post("/api/decks", response_model=Deck)
def create_deck(payload: DeckCreate):
    decks = load_decks()
    new_deck = Deck(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        creator=payload.creator,
        collaborators=payload.collaborators or []
    )
    decks.append(new_deck)
    save_decks(decks)
    return new_deck

@app.get("/api/decks/{deck_id}", response_model=Deck)
def get_deck(deck_id: str):
    decks = load_decks()
    for d in decks:
        if d.id == deck_id:
            return d
    raise HTTPException(status_code=404, detail="Deck not found")

@app.post("/api/decks/{deck_id}/cards", response_model=Card)
def add_card_to_deck(deck_id: str, card_data: dict):
    decks = load_decks()
    for d in decks:
        if d.id == deck_id:
            new_card = Card(
                deck_id=deck_id,
                type=card_data.get("type", "flashcard"),
                question=card_data.get("question"),
                answer=card_data.get("answer"),
                options=card_data.get("options"),
                explanation=card_data.get("explanation")
            )
            d.cards.append(new_card)
            save_decks(decks)
            return new_card
    raise HTTPException(status_code=404, detail="Deck not found")

@app.post("/api/decks/{deck_id}/mindmap")
def get_deck_mindmap(deck_id: str):
    decks = load_decks()
    for d in decks:
        if d.id == deck_id:
            return generate_mindmap(d)
    raise HTTPException(status_code=404, detail="Deck not found")

@app.get("/api/materials", response_model=List[Material])
def get_materials():
    return load_materials()

@app.post("/api/materials/upload", response_model=Material)
async def upload_material(file: UploadFile = File(...)):
    content_bytes = await file.read()
    text = extract_text_from_file(content_bytes, file.filename or "uploaded.txt")
    chunks = chunk_text(text)
    
    material = Material(
        filename=file.filename or "uploaded_syllabus.txt",
        content=text,
        chunk_count=len(chunks)
    )
    materials = load_materials()
    materials.append(material)
    save_materials(materials)
    return material

@app.post("/api/decks/generate", response_model=Deck)
def generate_deck(req: GenerateRequest):
    materials = load_materials()
    material_texts = [m.content for m in materials]
    if req.material_id:
        matched = [m.content for m in materials if m.id == req.material_id]
        if matched:
            material_texts = matched
            
    ai_data = generate_ai_deck(req.topic, req.card_type, req.count, material_texts)
    
    cards = []
    for c in ai_data.get("cards", []):
        cards.append(Card(
            deck_id="", # Will populate after deck creation
            type=c.get("type", "flashcard"),
            question=c.get("question"),
            answer=c.get("answer"),
            options=c.get("options"),
            explanation=c.get("explanation")
        ))
        
    new_deck = Deck(
        title=ai_data.get("title", f"Study Deck: {req.topic}"),
        description=ai_data.get("description", "AI Generated Study Deck"),
        category=ai_data.get("category", "General"),
        creator="EduCards AI",
        cards=[]
    )
    
    for card in cards:
        card.deck_id = new_deck.id
        new_deck.cards.append(card)
        
    decks = load_decks()
    decks.append(new_deck)
    save_decks(decks)
    return new_deck

@app.post("/api/ai/explain")
def explain_answer(req: ExplainRequest):
    explanation = generate_ai_explanation(
        req.question,
        req.user_answer,
        req.correct_answer,
        req.understanding_level,
        hint_level=req.hint_level,
        learner_attempt=req.learner_attempt
    )
    return {"explanation": explanation}

# Mount static files for frontend if directory exists
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
