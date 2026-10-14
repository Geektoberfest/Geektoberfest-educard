from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_static_index_serves():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Issue 3 Acceptance criteria checks:
    # 1. Think First toggle in settings and practice view
    assert "Think First" in html
    assert 'id="settings-think-first"' in html
    assert 'id="practice-think-first-toggle"' in html
    
    # 2. Recall attempt input and gated flip buttons
    assert 'id="fc-recall-input"' in html
    assert 'id="fc-flip-btn"' in html
    assert 'disabled' in html
    assert 'id="fc-idk-btn"' in html
    assert "I don't know" in html
    
    # 3. User attempt display after flipping
    assert 'id="fc-user-attempt-display"' in html

def test_static_css_contains_recall_styles():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    css = response.text
    assert ".user-attempt-box" in css
    assert ".recall-section" in css
    assert ".toggle-container" in css

def test_static_js_contains_think_first_and_gated_flip_logic():
    response = client.get("/static/app.js")
    assert response.status_code == 200
    js = response.text
    assert "thinkFirstEnabled" in js
    assert "toggleThinkFirst" in js
    assert "handleIdk" in js
    assert "onRecallInput" in js
    assert "flipFlashcard" in js
    assert "fc-user-attempt-display" in js
