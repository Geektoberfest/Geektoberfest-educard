from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_static_html_contains_confidence_and_session_summary_elements():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    
    # 1. Confidence selector and submit button
    assert 'id="mcq-confidence-section"' in html
    assert 'data-level="Guessing"' in html
    assert 'data-level="Unsure"' in html
    assert 'data-level="Sure"' in html
    assert 'id="mcq-submit-btn"' in html
    assert 'disabled' in html
    
    # 2. Confident but wrong warning badge in explainer
    assert 'id="explainer-priority-badge"' in html
    assert "Confident but Wrong" in html
    
    # 3. Session summary count & modal
    assert 'id="stats-confident-wrong-count"' in html
    assert 'id="session-summary-modal"' in html
    assert 'id="summary-confident-wrong-cards"' in html
    
    # 4. Think First toggle
    assert 'id="setting-think-first"' in html

def test_static_css_contains_confidence_and_selection_styles():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    css = response.text
    assert ".confidence-btn.active" in css
    assert ".mcq-option.selected" in css
    assert ".toggle-container" in css

def test_static_js_contains_confidence_logic():
    response = client.get("/static/app.js")
    assert response.status_code == 200
    js = response.text
    assert "selectConfidence" in js
    assert "selectMcqOption" in js
    assert "submitMcqAnswer" in js
    assert "sessionStats" in js
    assert "confidentButWrong" in js
    assert "openSessionSummaryModal" in js
