from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_service import _get_canned_explanation

client = TestClient(app)

def test_ai_explain():
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "understanding_level": "ELI5"
    })
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data

def test_ai_explain_default_hint_level(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "understanding_level": "ELI5"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Mitochondria" in data["explanation"]
    assert "The correct answer is 'Mitochondria'" in data["explanation"]

@pytest.mark.parametrize("level", [1, 2, 3])
def test_ai_explain_levels_no_correct_answer(monkeypatch, level):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "understanding_level": "Beginner",
        "hint_level": level
    })
    assert response.status_code == 200
    data = response.json()
    assert "mitochondria" not in data["explanation"].lower()

def test_ai_explain_level_4_full_explanation(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "understanding_level": "Beginner",
        "hint_level": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert "Mitochondria" in data["explanation"]
    assert "The correct answer is 'Mitochondria'" in data["explanation"]

@pytest.mark.parametrize("invalid_level", [0, 5])
def test_ai_explain_invalid_hint_level(invalid_level):
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "hint_level": invalid_level
    })
    assert response.status_code == 422

def test_ai_explain_with_learner_attempt(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/ai/explain", json={
        "question": "What is the powerhouse of the cell?",
        "user_answer": "Nucleus",
        "correct_answer": "Mitochondria",
        "understanding_level": "Beginner",
        "hint_level": 2,
        "learner_attempt": "I thought the nucleus produces energy"
    })
    assert response.status_code == 200
    data = response.json()
    assert "mitochondria" not in data["explanation"].lower()

@pytest.mark.parametrize("level", [1, 2, 3])
def test_ai_explain_leak_guard(monkeypatch, level):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    mock_response = MagicMock()
    mock_response.text = "The secret is Mitochondria which powers everything."
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    monkeypatch.setattr("google.genai.Client", lambda api_key: mock_client)

    question = "What is the powerhouse of the cell?"
    user_answer = "Nucleus"
    correct_answer = "Mitochondria"
    understanding_level = "Beginner"

    response = client.post("/api/ai/explain", json={
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "understanding_level": understanding_level,
        "hint_level": level
    })
    assert response.status_code == 200
    data = response.json()
    assert "mitochondria" not in data["explanation"].lower()
    expected_canned = _get_canned_explanation(question, user_answer, correct_answer, understanding_level, level)
    assert data["explanation"] == expected_canned
