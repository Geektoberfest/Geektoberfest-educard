# Hint Ladder Feature Changes (Issue #5)

This document details the implementation of [Issue #5: Hint ladder for /api/ai/explain](https://github.com/Geektoberfest/Geektoberfest-educard/issues/5).

---

## Summary of Changes and Rationale

Previously, `/api/ai/explain` returned the full answer explanation immediately upon answering a question incorrectly. This gave learners no chance to self-correct or receive progressive assistance.

To improve active recall and learning retention, this feature implements a 4-level staged hint ladder:

| Level | Content | Behavior |
|---|---|---|
| 1 | Guiding Question | Prompts the learner to reflect without revealing or defining the answer. |
| 2 | Conceptual Hint | Highlights underlying rules, mechanisms, or principles without stating the answer. |
| 3 | Partial Worked Step | Outlines the first step in solving/reasoning, stopping before conclusions. |
| 4 | Full Explanation | The complete explanation explaining why the attempt was incorrect and what the correct answer is. |

---

## Per-File Changes

### 1. `backend/models.py`
- **`ExplainRequest`**:
  - `hint_level: int = Field(default=4, ge=1, le=4)`: Accepts hint level between 1 and 4. Defaults to 4 to preserve backwards compatibility for existing clients. Any value outside 1–4 triggers a validation error (HTTP 422).
  - `learner_attempt: Optional[str] = None`: Optional string field capturing the learner's previous answer or revised attempt to tailor dynamic hints.

### 2. `backend/ai_service.py`
- **`HINT_INSTRUCTIONS`**:
  - Constant mapping hint levels 1–4 to specific system instructions. Levels 1–3 explicitly forbid revealing, stating, or paraphrasing the final answer.
- **`_get_canned_explanation(...)`**:
  - Deterministic fallback function returning level-appropriate canned text when `GEMINI_API_KEY` is absent or when an external API call fails.
  - Guarantees that levels 1–3 never leak the correct answer, while level 4 preserves the original fallback text.
- **`generate_ai_explanation(...)`**:
  - Signature updated to `(question: str, user_answer: str, correct_answer: str, understanding_level: str, hint_level: int = 4, learner_attempt: Optional[str] = None) -> str`.
  - Injects `learner_attempt` into the prompt if provided.
  - Constructs level-specific prompts for levels 1–3 forbidding answer disclosure.
  - Retains the exact original prompt and behavior when `hint_level == 4`.
  - Includes a response leak-guard check: if a Gemini response at levels 1–3 contains `correct_answer`, it safely falls back to `_get_canned_explanation`.

### 3. `backend/main.py`
- **`explain_answer(req: ExplainRequest)`** (`POST /api/ai/explain`):
  - Passes `hint_level=req.hint_level` and `learner_attempt=req.learner_attempt` into `generate_ai_explanation`.
  - Preserves the response payload format `{"explanation": explanation}` for seamless backward compatibility.

### 4. `backend/test_explain.py`
- Added comprehensive unit and integration tests:
  - `test_ai_explain_default_hint_level`: Verifies default requests (without `hint_level`) behave as level 4 and include the correct answer.
  - `test_ai_explain_levels_no_correct_answer`: Verifies levels 1, 2, and 3 do not contain the correct answer text in the explanation.
  - `test_ai_explain_level_4_full_explanation`: Verifies level 4 returns the complete explanation with the correct answer.
  - `test_ai_explain_invalid_hint_level`: Verifies invalid hint levels (0, 5) return HTTP 422.
  - `test_ai_explain_with_learner_attempt`: Verifies `learner_attempt` is accepted and processed cleanly.
  - `test_ai_explain_leak_guard`: Tests mock GenAI response attempting to leak the correct answer at levels 1–3 and ensures fallback is triggered.

### 5. `README.md`
- Updated API Endpoints section for `POST /api/ai/explain`:
  - Documented new `hint_level` (int 1-4, default 4) and `learner_attempt` (str, optional) parameters.
  - Added hint ladder levels table.
  - Provided example JSON request and response payloads.

### 6. `frontend/index.html`
- Added a `#hint-btn` button (`Give me a hint`) inside `#explainer-modal`.
- Updated container `#explainer-text` to display incremental hint items.

### 7. `frontend/style.css`
- Added `.hint-item` styles with clean borders and spacing matching EduCards design tokens.

### 8. `frontend/app.js`
- State variables `hintLevel` and `displayedHints` to track progressive hint stages.
- `resetHintState()`: Resets the ladder to level 0 when opening the explainer modal, flipping cards, or switching practice decks.
- `updateHintButton()`: Manages button labels ("Give me a hint" for levels 0–2, "Show full explanation" at level 3, hidden/disabled after level 4).
- `renderHints()`: Displays each hint stage with appropriate badges.
- `requestNextHint()`: Fetches the next staged level from `/api/ai/explain` and appends it to the modal display.
- `fetchAiExplanation()`: Re-fetches the current active hint level if the learner alters the understanding level dropdown.

---

## Example Requests and Responses

### Level 1: Guiding Question
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the powerhouse of the cell?",
    "user_answer": "Nucleus",
    "correct_answer": "Mitochondria",
    "understanding_level": "Beginner",
    "hint_level": 1
  }'
```
Response:
```json
{
  "explanation": "At a Beginner level: Consider 'What is the powerhouse of the cell?'. What key concept or mechanism plays the primary role here?"
}
```

### Level 2: Conceptual Hint
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the powerhouse of the cell?",
    "user_answer": "Nucleus",
    "correct_answer": "Mitochondria",
    "understanding_level": "Beginner",
    "hint_level": 2,
    "learner_attempt": "Nucleus"
  }'
```
Response:
```json
{
  "explanation": "At a Beginner level: Focus on the foundational concepts behind 'What is the powerhouse of the cell?'. Recall the core rule or definition."
}
```

### Level 3: Partial Step
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the powerhouse of the cell?",
    "user_answer": "Nucleus",
    "correct_answer": "Mitochondria",
    "understanding_level": "Beginner",
    "hint_level": 3
  }'
```
Response:
```json
{
  "explanation": "At a Beginner level: Step 1: Break down 'What is the powerhouse of the cell?' into its components and eliminate what doesn't fit."
}
```

### Level 4: Full Explanation
Request:
```bash
curl -s -X POST http://127.0.0.1:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the powerhouse of the cell?",
    "user_answer": "Nucleus",
    "correct_answer": "Mitochondria",
    "understanding_level": "Beginner",
    "hint_level": 4
  }'
```
Response:
```json
{
  "explanation": "At a Beginner level: Your answer 'Nucleus' is not quite right. The correct answer is 'Mitochondria'. Here's why: EduCards AI notes that 'Mitochondria' satisfies all conditions of the question 'What is the powerhouse of the cell?'."
}
```

---

## Backwards Compatibility

- **Omitted `hint_level`**: Defaults to 4. Existing clients calling `/api/ai/explain` without `hint_level` receive the full explanation, identical to previous behavior.
- **Payload Shape**: The response continues to return `{"explanation": "..."}` without breaking any existing clients.
- **Fallback Compatibility**: Level 4 fallback produces the exact same explanation string as before.

---

## How to Test

### Automated Tests
Run pytest across the suite:
```bash
python -m pytest backend/ -v
```
All 19 tests will pass.

### Manual Verification
1. Start the server (with or without `GEMINI_API_KEY`):
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Open `http://127.0.0.1:8000` in the browser.
3. Start practice on any deck and answer an MCQ incorrectly.
4. Click "Give me a hint" to see Level 1, then Level 2, then Level 3.
5. Notice the button switches to "Show full explanation" at Level 3.
6. Click "Show full explanation" to see Level 4; verify the button is hidden after Level 4 is rendered.
