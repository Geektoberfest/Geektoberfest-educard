# EduCards 🎓

EduCards is a collaborative, AI-powered study assistant designed to help students and educators generate interactive flashcards and multiple-choice questions (MCQs), ingest syllabus materials for Retrieval-Augmented Generation (RAG), practice interactively, and receive adaptive AI explanations for incorrect answers.

---

## 🌟 Key Features

1. **Gen AI Study Deck Generator:** Automatically generate high-quality flashcard and MCQ decks on any topic using Google Gemini.
2. **Syllabus RAG Ingestion:** Upload lecture notes, syllabi, or textbooks (PDF or TXT) to ground AI deck generation directly in your coursework.
3. **Interactive Practice Mode:** Practice decks with interactive flashcard flipping and MCQ quiz mode with instant validation.
4. **Adaptive AI Explainer:** When you answer a question incorrectly, trigger the AI tutor to explain the concept tailored to your exact understanding level (ELI5, Beginner, Intermediate, or Advanced Expert).
5. **Clean, Modern UI:** Built with Vanilla HTML5, CSS3 (solid colors, CSS variables, zero-gradient minimal aesthetic), and Vanilla JavaScript.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, FastAPI, Pydantic v2, Uvicorn, Google GenAI SDK (`google-genai`), PyPDF
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Storage:** Local JSON persistence (`data/decks.json`)
- **Testing:** Pytest, HTTPX

---

## 📁 Project Structure

```text
ps_2_gfg/
├── backend/
│   ├── ai_service.py      # Gemini AI client & prompt engineering
│   ├── main.py            # FastAPI application & API endpoints
│   ├── models.py          # Pydantic data models (Deck, Card, Material)
│   ├── rag.py             # PDF/Text extraction & RAG chunking
│   ├── storage.py         # JSON storage persistence helper
│   ├── requirements.txt   # Backend Python dependencies
│   └── test_*.py          # Unit and integration test suite
├── data/
│   └── decks.json         # Local JSON store for study decks
├── frontend/
│   ├── index.html         # Single-page application shell & modals
│   ├── style.css          # Solid color design system & UI styles
│   └── app.js             # Frontend router, state, and API client
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager
- (Optional) `GEMINI_API_KEY` environment variable from Google AI Studio. *(Note: If no API key is set, EduCards automatically falls back to deterministic mock decks and canned AI explanations for seamless local development).*
- (Optional) `GROQ_API_KEY` environment variable from Groq for mindmap generation (`llama-3.3-70b-versatile`). *(Falls back to deterministic mock mindmaps if not set).*

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/educards.git
   cd educards
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

---

## 🏃 Running the Application

Start the FastAPI backend server using Uvicorn:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and visit:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🧪 Running Tests

Run the complete test suite with `pytest`:

```bash
python -m pytest backend/ -v
```

---

## 🔌 API Endpoints

- `GET /api/health` — Health check
- `GET /api/decks` — List all study decks
- `POST /api/decks` — Create a new study deck
- `GET /api/decks/{id}` — Get deck details
- `POST /api/decks/generate` — Generate study deck using Gen AI & RAG
- `GET /api/materials` — List uploaded RAG materials
- `POST /api/materials/upload` — Upload and index a PDF/TXT syllabus
- `POST /api/ai/explain` — Get adaptive AI explanation or staged hint ladder for incorrect answers.
  - Parameters: `question` (str), `user_answer` (str), `correct_answer` (str), `understanding_level` (str, default `"Beginner"`), `hint_level` (int 1-4, default `4`), `learner_attempt` (str, optional).

  | hint_level | Content |
  |---|---|
  | 1 | A guiding question, no answer |
  | 2 | A conceptual hint |
  | 3 | A partial worked step |
  | 4 | The full explanation (default) |

  Example request:
  ```json
  {
    "question": "What is the powerhouse of the cell?",
    "user_answer": "Nucleus",
    "correct_answer": "Mitochondria",
    "understanding_level": "Beginner",
    "hint_level": 1,
    "learner_attempt": "Nucleus"
  }
  ```

  Example response:
  ```json
  {
    "explanation": "At a Beginner level: Consider 'What is the powerhouse of the cell?'. What key concept or mechanism plays the primary role here?"
  }
  ```
- `POST /api/decks/{id}/mindmap` — Generate mindmap for study deck using Gen AI

---

## 📄 License

MIT License
