let currentDecks = [];
let currentMaterials = [];
let currentDeck = null;
let currentCardIndex = 0;
let currentWrongContext = null;
let hintLevel = 0;
let displayedHints = [];
let thinkFirstEnabled = localStorage.getItem("thinkFirstEnabled") !== "false";
let currentRecallAttempt = "";
let isFlashcardFlipped = false;

document.addEventListener("DOMContentLoaded", () => {
  loadDecks();
  loadMaterials();
  syncThinkFirstCheckboxes();
});

function switchView(viewName) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  
  const viewEl = document.getElementById(`view-${viewName}`);
  if (viewEl) viewEl.classList.add("active");
  
  const navEl = document.getElementById(`nav-${viewName}`);
  if (navEl) navEl.classList.add("active");
  
  if (viewName === "dashboard" || viewName === "decks") {
    loadDecks();
  } else if (viewName === "materials") {
    loadMaterials();
  }
}

async function loadDecks() {
  try {
    const res = await fetch("/api/decks");
    currentDecks = await res.json();
    renderDecks();
  } catch (err) {
    console.error("Failed to load decks", err);
  }
}

function renderDecks() {
  const grid = document.getElementById("decks-grid");
  const dashGrid = document.getElementById("dashboard-decks-grid");
  
  if (!currentDecks.length) {
    const emptyHtml = `<p style="color: var(--text-secondary);">No study decks yet. Click "+ Gen AI Deck" to create one!</p>`;
    if (grid) grid.innerHTML = emptyHtml;
    if (dashGrid) dashGrid.innerHTML = emptyHtml;
    return;
  }

  const html = currentDecks.map(deck => `
    <div class="card">
      <div>
        <span class="badge">${deck.category}</span>
        <h3>${deck.title}</h3>
        <p>${deck.description}</p>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">🃏 ${deck.cards.length} Cards &bull; By ${deck.creator}</p>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn" onclick="startPractice('${deck.id}')" style="flex: 1;">Practice</button>
        <button class="btn btn-secondary" onclick="openMindmapForDeck('${deck.id}')">Mindmap</button>
      </div>
    </div>
  `).join("");

  if (grid) grid.innerHTML = html;
  if (dashGrid) dashGrid.innerHTML = html;
}

async function loadMaterials() {
  try {
    const res = await fetch("/api/materials");
    currentMaterials = await res.json();
    renderMaterials();
    updateMaterialDropdown();
  } catch (err) {
    console.error("Failed to load materials", err);
  }
}

function renderMaterials() {
  const listEl = document.getElementById("materials-list");
  if (!currentMaterials.length) {
    listEl.innerHTML = `<p style="color: var(--text-secondary);">No study materials uploaded yet.</p>`;
    return;
  }

  listEl.innerHTML = currentMaterials.map(m => `
    <div style="padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
      <div>
        <strong>📄 ${m.filename}</strong>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0;">Chunks: ${m.chunk_count} &bull; Uploaded: ${new Date(m.uploaded_at).toLocaleDateString()}</p>
      </div>
      <span class="badge" style="background: #CCFBF1; color: #134E4A; margin-bottom: 0;">Indexed for RAG</span>
    </div>
  `).join("");
}

function updateMaterialDropdown() {
  const select = document.getElementById("gen-material");
  if (!select) return;
  
  let html = `<option value="">-- Use General Knowledge / All Materials --</option>`;
  currentMaterials.forEach(m => {
    html += `<option value="${m.id}">${m.filename} (${m.chunk_count} chunks)</option>`;
  });
  select.innerHTML = html;
}

async function uploadMaterial(event) {
  event.preventDefault();
  const fileInput = document.getElementById("material-file");
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/materials/upload", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      fileInput.value = "";
      loadMaterials();
      alert("Material successfully uploaded and indexed for RAG!");
    } else {
      alert("Failed to upload material.");
    }
  } catch (err) {
    console.error("Upload error", err);
    alert("Error uploading material.");
  }
}

function openGenModal() {
  document.getElementById("gen-modal").classList.add("active");
}

function closeGenModal() {
  document.getElementById("gen-modal").classList.remove("active");
}

async function generateDeck(event) {
  event.preventDefault();
  const topic = document.getElementById("gen-topic").value;
  const cardType = document.getElementById("gen-type").value;
  const count = parseInt(document.getElementById("gen-count").value);
  const materialId = document.getElementById("gen-material").value;

  closeGenModal();
  
  // Show loading indicator
  const grid = document.getElementById("decks-grid");
  if (grid) grid.innerHTML = `<p style="color: var(--accent); font-weight: 600;">Generating AI study deck with RAG context...</p>`;

  try {
    const res = await fetch("/api/decks/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, card_type: cardType, count, material_id: materialId || null })
    });

    if (res.ok) {
      const deck = await res.json();
      loadDecks();
      startPractice(deck.id);
    } else {
      alert("Failed to generate deck.");
      loadDecks();
    }
  } catch (err) {
    console.error("Generation error", err);
    alert("Error generating deck.");
    loadDecks();
  }
}

function startPractice(deckId) {
  currentDeck = currentDecks.find(d => d.id === deckId);
  if (!currentDeck || !currentDeck.cards.length) {
    alert("This deck has no cards.");
    return;
  }
  currentCardIndex = 0;
  resetHintState();
  document.getElementById("practice-deck-title").innerText = currentDeck.title;
  switchView("practice");
  renderCard();
}

function renderCard() {
  if (!currentDeck || !currentDeck.cards.length) return;
  const card = currentDeck.cards[currentCardIndex];
  
  document.getElementById("practice-progress").innerText = `Card ${currentCardIndex + 1} of ${currentDeck.cards.length}`;
  
  const fcContainer = document.getElementById("flashcard-container");
  const mcqContainer = document.getElementById("mcq-container");
  
  if (card.type === "mcq") {
    fcContainer.style.display = "none";
    mcqContainer.style.display = "block";
    
    document.getElementById("mcq-question").innerText = card.question;
    const optionsEl = document.getElementById("mcq-options");
    
    optionsEl.innerHTML = (card.options || [card.answer, "Option B", "Option C", "Option D"]).map(opt => `
      <div class="mcq-option" onclick="checkMcqAnswer('${escapeQuote(opt)}', '${escapeQuote(card.answer)}', '${escapeQuote(card.question)}')">${opt}</div>
    `).join("");
  } else {
    fcContainer.style.display = "flex";
    mcqContainer.style.display = "none";
    
    isFlashcardFlipped = false;
    currentRecallAttempt = "";
    fcContainer.classList.remove("revealed");
    document.getElementById("fc-question").innerText = card.question;
    document.getElementById("fc-answer").innerText = card.answer;

    const recallInput = document.getElementById("fc-recall-input");
    if (recallInput) recallInput.value = "";
    const flipBtn = document.getElementById("fc-flip-btn");
    if (flipBtn) flipBtn.disabled = true;

    const ansContainer = document.getElementById("fc-answer-container");
    if (ansContainer) ansContainer.style.display = "none";
    const attemptDisplay = document.getElementById("fc-user-attempt-display");
    if (attemptDisplay) attemptDisplay.style.display = "none";

    syncThinkFirstCheckboxes();
    updateFlashcardRecallUI();
  }
}

function updateFlashcardRecallUI() {
  const recallSec = document.getElementById("fc-recall-section");
  const hintText = document.getElementById("fc-hint-text");
  const flipBtn = document.getElementById("fc-flip-btn");

  if (!isFlashcardFlipped) {
    if (thinkFirstEnabled) {
      if (recallSec) recallSec.style.display = "block";
      if (flipBtn) flipBtn.disabled = !currentRecallAttempt.trim();
      if (hintText) hintText.innerText = '(Type attempt or tap "I don\'t know" to flip)';
    } else {
      if (recallSec) recallSec.style.display = "none";
      if (hintText) hintText.innerText = "(Click card to reveal answer)";
    }
  }
}

function onRecallInput(value) {
  currentRecallAttempt = value;
  const flipBtn = document.getElementById("fc-flip-btn");
  if (flipBtn) {
    flipBtn.disabled = !value.trim();
  }
}

function onRecallKeydown(event) {
  if (event.key === "Enter" && currentRecallAttempt.trim()) {
    event.preventDefault();
    flipFlashcard();
  }
}

function handleIdk() {
  currentRecallAttempt = "I don't know";
  const recallInput = document.getElementById("fc-recall-input");
  if (recallInput) recallInput.value = "I don't know";
  const flipBtn = document.getElementById("fc-flip-btn");
  if (flipBtn) flipBtn.disabled = false;
  flipFlashcard();
}

function handleCardClick(event) {
  if (!thinkFirstEnabled) {
    flipFlashcard();
    return;
  }
  if (isFlashcardFlipped) {
    flipFlashcard();
  } else {
    const recallInput = document.getElementById("fc-recall-input");
    if (recallInput) recallInput.focus();
  }
}

function flipFlashcard() {
  if (thinkFirstEnabled && !isFlashcardFlipped && !currentRecallAttempt.trim()) {
    return;
  }

  isFlashcardFlipped = !isFlashcardFlipped;

  const fcContainer = document.getElementById("flashcard-container");
  const ansContainer = document.getElementById("fc-answer-container");
  const attemptDisplay = document.getElementById("fc-user-attempt-display");
  const recallSec = document.getElementById("fc-recall-section");
  const hintText = document.getElementById("fc-hint-text");

  if (isFlashcardFlipped) {
    fcContainer.classList.add("revealed");
    if (thinkFirstEnabled && currentRecallAttempt.trim()) {
      attemptDisplay.style.display = "block";
      attemptDisplay.innerHTML = `<strong>Your Attempt:</strong> ${escapeHtml(currentRecallAttempt.trim())}`;
    } else {
      attemptDisplay.style.display = "none";
    }
    if (recallSec) recallSec.style.display = "none";
    if (ansContainer) ansContainer.style.display = "block";
    if (hintText) hintText.innerText = "(Click card to flip back)";
  } else {
    fcContainer.classList.remove("revealed");
    if (ansContainer) ansContainer.style.display = "none";
    if (attemptDisplay) attemptDisplay.style.display = "none";
    if (thinkFirstEnabled) {
      if (recallSec) recallSec.style.display = "block";
      const flipBtn = document.getElementById("fc-flip-btn");
      if (flipBtn) flipBtn.disabled = !currentRecallAttempt.trim();
      if (hintText) hintText.innerText = '(Type attempt or tap "I don\'t know" to flip)';
    } else {
      if (recallSec) recallSec.style.display = "none";
      if (hintText) hintText.innerText = "(Click card to reveal answer)";
    }
  }
}

function checkMcqAnswer(selected, correct, question) {
  const optionsEl = document.getElementById("mcq-options");
  const opts = optionsEl.querySelectorAll(".mcq-option");
  
  opts.forEach(el => {
    el.style.pointerEvents = "none";
    if (el.innerText.trim() === correct.trim()) {
      el.classList.add("correct");
    } else if (el.innerText.trim() === selected.trim() && selected.trim() !== correct.trim()) {
      el.classList.add("incorrect");
    }
  });

  if (selected.trim() === correct.trim()) {
    // Correct! Wait 1.2s and go next
    setTimeout(() => {
      nextCard();
    }, 1200);
  } else {
    // Incorrect! Trigger AI Explainer modal
    currentWrongContext = {
      question,
      user_answer: selected,
      correct_answer: correct
    };
    setTimeout(() => {
      openExplainerModal();
    }, 600);
  }
}

function nextCard() {
  if (!currentDeck) return;
  resetHintState();
  currentCardIndex = (currentCardIndex + 1) % currentDeck.cards.length;
  renderCard();
}

function prevCard() {
  if (!currentDeck) return;
  resetHintState();
  currentCardIndex = (currentCardIndex - 1 + currentDeck.cards.length) % currentDeck.cards.length;
  renderCard();
}

function openExplainerModal() {
  if (!currentWrongContext) return;
  resetHintState();
  document.getElementById("explainer-question-title").innerText = currentWrongContext.question;
  document.getElementById("explainer-summary").innerText = `You answered "${currentWrongContext.user_answer}". The correct answer is "${currentWrongContext.correct_answer}".`;
  document.getElementById("explainer-modal").classList.add("active");
}

function closeExplainerModal() {
  document.getElementById("explainer-modal").classList.remove("active");
}

function resetHintState() {
  hintLevel = 0;
  displayedHints = [];
  renderHints();
  updateHintButton();
}

function updateHintButton() {
  const btn = document.getElementById("hint-btn");
  if (!btn) return;
  if (hintLevel >= 4) {
    btn.style.display = "none";
    btn.disabled = true;
  } else {
    btn.style.display = "inline-flex";
    btn.disabled = false;
    if (hintLevel === 3) {
      btn.innerText = "Show full explanation";
    } else {
      btn.innerText = "Give me a hint";
    }
  }
}

function renderHints() {
  const container = document.getElementById("explainer-text");
  if (!container) return;
  if (!displayedHints.length) {
    container.innerText = "Click 'Give me a hint' to get started.";
    return;
  }
  container.innerHTML = displayedHints.map(h => `
    <div class="hint-item">
      <strong style="color: var(--accent);">${h.level === 4 ? "Full Explanation" : `Hint ${h.level}`}:</strong>
      <div style="margin-top: 0.25rem; color: var(--text-primary);">${escapeXml(h.text)}</div>
    </div>
  `).join("");
}

async function requestNextHint() {
  if (hintLevel >= 4 || !currentWrongContext) return;
  const targetLevel = hintLevel + 1;
  const btn = document.getElementById("hint-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Loading...";
  }

  const level = document.getElementById("understanding-level").value;
  try {
    const res = await fetch("/api/ai/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: currentWrongContext.question,
        user_answer: currentWrongContext.user_answer,
        correct_answer: currentWrongContext.correct_answer,
        understanding_level: level,
        hint_level: targetLevel,
        learner_attempt: currentWrongContext.user_answer || null
      })
    });

    if (res.ok) {
      const data = await res.json();
      hintLevel = targetLevel;
      displayedHints.push({ level: hintLevel, text: data.explanation });
      renderHints();
    } else {
      alert("Failed to fetch hint.");
    }
  } catch (err) {
    console.error("Hint error", err);
    alert("Error fetching hint.");
  } finally {
    updateHintButton();
  }
}

async function fetchAiExplanation() {
  if (!currentWrongContext || hintLevel === 0) return;
  const level = document.getElementById("understanding-level").value;
  try {
    const res = await fetch("/api/ai/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: currentWrongContext.question,
        user_answer: currentWrongContext.user_answer,
        correct_answer: currentWrongContext.correct_answer,
        understanding_level: level,
        hint_level: hintLevel,
        learner_attempt: currentWrongContext.user_answer || null
      })
    });

    if (res.ok) {
      const data = await res.json();
      if (displayedHints.length > 0) {
        displayedHints[displayedHints.length - 1].text = data.explanation;
        renderHints();
      }
    }
  } catch (err) {
    console.error("Explainer error", err);
  }
}

function escapeQuote(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function openMindmapForDeck(deckId) {
  currentDeck = currentDecks.find(d => d.id === deckId);
  if (!currentDeck) return;
  openMindmap();
}

function closeMindmapModal() {
  const modal = document.getElementById("mindmap-modal");
  if (modal) modal.classList.remove("active");
}

async function openMindmap() {
  if (!currentDeck) return;
  const modal = document.getElementById("mindmap-modal");
  const titleEl = document.getElementById("mindmap-title");
  const container = document.getElementById("mindmap-container");

  titleEl.innerText = `${currentDeck.title} - Mindmap`;
  container.innerHTML = `<p style="color: var(--accent); font-weight: 600;">Generating mindmap...</p>`;
  modal.classList.add("active");

  try {
    const res = await fetch(`/api/decks/${currentDeck.id}/mindmap`, {
      method: "POST"
    });
    if (res.ok) {
      const data = await res.json();
      renderMindmapSvg(data);
    } else {
      container.innerHTML = `<p style="color: var(--danger);">Failed to load mindmap.</p>`;
    }
  } catch (err) {
    console.error("Mindmap error", err);
    container.innerHTML = `<p style="color: var(--danger);">Error loading mindmap.</p>`;
  }
}

function renderMindmapSvg(data) {
  const container = document.getElementById("mindmap-container");
  if (!container) return;

  const width = 740;
  const height = 460;
  const cx = width / 2;
  const cy = height / 2;
  const nodes = Array.isArray(data.nodes) ? data.nodes : [];
  const edges = Array.isArray(data.edges) ? data.edges : [];

  const positions = {};
  positions["root"] = { x: cx, y: cy };
  if (data.root) {
    positions[data.root] = { x: cx, y: cy };
  }

  const rx = 240;
  const ry = 150;
  nodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / nodes.length - Math.PI / 2;
    const nx = Math.round(cx + rx * Math.cos(angle));
    const ny = Math.round(cy + ry * Math.sin(angle));
    positions[node.id] = { x: nx, y: ny };
  });

  let linesHtml = "";
  const connectedNodes = new Set();
  edges.forEach(edge => {
    const p1 = positions[edge.from];
    const p2 = positions[edge.to];
    if (p1 && p2) {
      linesHtml += `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="#CBD5E1" stroke-width="2" />`;
      connectedNodes.add(edge.to);
      connectedNodes.add(edge.from);
    }
  });

  nodes.forEach(node => {
    if (!connectedNodes.has(node.id)) {
      const p = positions[node.id];
      if (p) {
        linesHtml += `<line x1="${cx}" y1="${cy}" x2="${p.x}" y2="${p.y}" stroke="#CBD5E1" stroke-width="2" />`;
      }
    }
  });

  const rootFull = data.root || "Topic";
  const rootLabel = truncate(rootFull, 22);
  let nodesHtml = `
    <g class="mindmap-root-node">
      <rect x="${cx - 95}" y="${cy - 24}" width="190" height="48" rx="8" fill="#0F172A" stroke="#0D9488" stroke-width="2" />
      <text x="${cx}" y="${cy}" fill="#FFFFFF" font-size="13" font-weight="bold" text-anchor="middle" dominant-baseline="central">${escapeXml(rootLabel)}</text>
      <title>${escapeXml(rootFull)}</title>
    </g>
  `;

  nodes.forEach(node => {
    const p = positions[node.id];
    const full = node.label || node.id;
    const label = truncate(full, 20);
    nodesHtml += `
      <g class="mindmap-child-node">
        <rect x="${p.x - 70}" y="${p.y - 20}" width="140" height="40" rx="6" fill="#FFFFFF" stroke="#0D9488" stroke-width="2" />
        <text x="${p.x}" y="${p.y}" fill="#1E293B" font-size="11" font-weight="600" text-anchor="middle" dominant-baseline="central">${escapeXml(label)}</text>
        <title>${escapeXml(full)}</title>
      </g>
    `;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" xmlns="http://www.w3.org/2000/svg" style="background: #F8FAFC; border-radius: 8px; border: 1px solid var(--border);">
      <g class="edges">${linesHtml}</g>
      <g class="nodes">${nodesHtml}</g>
    </svg>
  `;
}

function truncate(str, maxLen) {
  if (!str) return "";
  return str.length > maxLen ? str.slice(0, maxLen - 1) + "…" : str;
}

function escapeXml(unsafe) {
  if (!unsafe) return "";
  return String(unsafe).replace(/[<>&'"]/g, c => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '\'': return '&apos;';
      case '"': return '&quot;';
    }
  });
}
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function syncThinkFirstCheckboxes() {
  const practiceToggle = document.getElementById("practice-think-first-toggle");
  const settingsToggle = document.getElementById("settings-think-first");
  if (practiceToggle) practiceToggle.checked = thinkFirstEnabled;
  if (settingsToggle) settingsToggle.checked = thinkFirstEnabled;
}

function openSettingsModal() {
  syncThinkFirstCheckboxes();
  const modal = document.getElementById("settings-modal");
  if (modal) modal.classList.add("active");
}

function closeSettingsModal() {
  const modal = document.getElementById("settings-modal");
  if (modal) modal.classList.remove("active");
}

function toggleThinkFirst(checked) {
  thinkFirstEnabled = checked;
  localStorage.setItem("thinkFirstEnabled", checked ? "true" : "false");
  syncThinkFirstCheckboxes();
  if (currentDeck && currentDeck.cards && currentDeck.cards[currentCardIndex]?.type !== "mcq") {
    updateFlashcardRecallUI();
  }
}

