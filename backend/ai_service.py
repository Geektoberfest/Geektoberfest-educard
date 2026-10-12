import os
import json
from typing import List, Dict, Any, Optional
from backend.models import Card, Deck
from backend.rag import retrieve_relevant_context

def generate_ai_deck(topic: str, card_type: str, count: int, materials: List[str]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    context = retrieve_relevant_context(topic, materials)
    
    # Try using Google GenAI SDK if key exists
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Generate a study deck about '{topic}' with {count} cards of type '{card_type}'.
            Here is reference study material/syllabus context:
            {context}
            
            Return ONLY a valid JSON object with this exact structure:
            {{
              "title": "Study Deck Title",
              "description": "Short description",
              "category": "General",
              "cards": [
                {{
                  "type": "flashcard" or "mcq",
                  "question": "Question text",
                  "answer": "Correct answer",
                  "options": ["Option A", "Option B", "Option C", "Option D"] (required only for mcq, else omit or null),
                  "explanation": "Detailed explanation of the correct answer"
                }}
              ]
            }}
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip()
            # Clean markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            return data
        except Exception as e:
            print(f"Gemini API generation failed, falling back to mock: {e}")

    # Fallback mock generator
    cards = []
    for i in range(1, count + 1):
        if card_type == "mcq" or (card_type == "mixed" and i % 2 == 0):
            cards.append({
                "type": "mcq",
                "question": f"Sample MCQ {i} about {topic}?",
                "answer": "Option A",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "explanation": f"Option A is correct because it directly relates to core concepts of {topic}."
            })
        else:
            cards.append({
                "type": "flashcard",
                "question": f"What is key concept {i} of {topic}?",
                "answer": f"Core definition and mechanism of {topic} part {i}.",
                "options": None,
                "explanation": f"This concept is foundational when studying {topic}."
            })
            
    return {
        "title": f"Mastering {topic}",
        "description": f"AI-generated study deck covering {topic} using uploaded syllabus materials.",
        "category": "Study Deck",
        "cards": cards
    }

HINT_INSTRUCTIONS = {
    1: "Ask ONE guiding question that points the learner toward the idea; give no answer, no explanation, no definition of the answer.",
    2: "Give a short conceptual hint naming the underlying concept or rule, without stating the answer.",
    3: "Show only the first partial step of the working or reasoning, and stop before the conclusion.",
    4: "Provide a clear, encouraging explanation addressing:\n1. Why the student's answer ({user_answer}) is incorrect.\n2. What the correct answer ({correct_answer}) is and why.\n3. Explained tailored precisely to the '{understanding_level}' level.",
}

def _get_canned_explanation(
    question: str,
    user_answer: str,
    correct_answer: str,
    understanding_level: str,
    hint_level: int = 4
) -> str:
    if hint_level == 1:
        return f"At a {understanding_level} level: Consider '{question}'. What key concept or mechanism plays the primary role here?"
    elif hint_level == 2:
        return f"At a {understanding_level} level: Focus on the foundational concepts behind '{question}'. Recall the core rule or definition."
    elif hint_level == 3:
        return f"At a {understanding_level} level: Step 1: Break down '{question}' into its components and eliminate what doesn't fit."
    return (
        f"At a {understanding_level} level: Your answer '{user_answer}' is not quite right. "
        f"The correct answer is '{correct_answer}'. "
        f"Here's why: EduCards AI notes that '{correct_answer}' satisfies all conditions of the question '{question}'."
    )

def generate_ai_explanation(
    question: str,
    user_answer: str,
    correct_answer: str,
    understanding_level: str,
    hint_level: int = 4,
    learner_attempt: Optional[str] = None
) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            attempt_line = f"\nLearner's Attempt: {learner_attempt.strip()}" if (learner_attempt and learner_attempt.strip()) else ""
            if hint_level == 4:
                prompt = f"""
            The student answered a study question incorrectly.
            Question: {question}
            Student's Answer: {user_answer}{attempt_line}
            Correct Answer: {correct_answer}
            Target Understanding Level: {understanding_level} (e.g. ELI5 = Explain like I am 5, Beginner, Intermediate, Advanced)
            
            Provide a clear, encouraging explanation addressing:
            1. Why the student's answer ({user_answer}) is incorrect.
            2. What the correct answer ({correct_answer}) is and why.
            3. Explained tailored precisely to the '{understanding_level}' level.
            """
            else:
                instruction = HINT_INSTRUCTIONS.get(hint_level, "")
                prompt = f"""
            The student answered a study question incorrectly.
            Question: {question}
            Student's Answer: {user_answer}{attempt_line}
            Correct Answer: {correct_answer}
            Target Understanding Level: {understanding_level} (e.g. ELI5 = Explain like I am 5, Beginner, Intermediate, Advanced)
            
            Instruction: {instruction}
            Never reveal, state, or paraphrase the correct answer.
            Explain tailored precisely to the '{understanding_level}' level.
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip()
            if 1 <= hint_level <= 3 and correct_answer and correct_answer.strip():
                if correct_answer.strip().lower() in text.lower():
                    return _get_canned_explanation(question, user_answer, correct_answer, understanding_level, hint_level)
            return text
        except Exception as e:
            print(f"Gemini explain API failed, using fallback: {e}")

    # Fallback explanation
    return _get_canned_explanation(question, user_answer, correct_answer, understanding_level, hint_level)

def generate_mindmap(deck: Any) -> Dict[str, Any]:
    deck_title = getattr(deck, "title", None) or (deck.get("title") if isinstance(deck, dict) else "Study Deck")
    cards = getattr(deck, "cards", None) or (deck.get("cards") if isinstance(deck, dict) else [])

    card_fronts = []
    for c in cards:
        if hasattr(c, "question") and c.question:
            card_fronts.append(c.question)
        elif isinstance(c, dict) and c.get("question"):
            card_fronts.append(c["question"])

    def _fallback_mindmap() -> Dict[str, Any]:
        root = deck_title or "Study Deck"
        nodes = []
        edges = []
        if card_fronts:
            for i, front in enumerate(card_fronts, 1):
                nid = f"n{i}"
                nodes.append({"id": nid, "label": front})
                edges.append({"from": "root", "to": nid})
        else:
            nodes.append({"id": "n1", "label": "Key Concepts"})
            edges.append({"from": "root", "to": "n1"})
        return {
            "root": root,
            "nodes": nodes,
            "edges": edges
        }

    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            card_list_text = "\n".join(f"- {front}" for front in card_fronts) if card_fronts else "No specific cards provided."
            prompt = f"""
Generate a structured mindmap for the study deck '{deck_title}'.
Here are the key flashcard questions/concepts from the deck:
{card_list_text}

Return ONLY a valid JSON object with this exact schema:
{{
  "root": "<topic>",
  "nodes": [
    {{"id": "n1", "label": "..."}}
  ],
  "edges": [
    {{"from": "n1", "to": "n2"}}
  ]
}}
"""
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            raw_text = chat_completion.choices[0].message.content or ""
            text = raw_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())

            if (
                isinstance(data, dict)
                and "root" in data
                and isinstance(data["root"], str)
                and "nodes" in data
                and isinstance(data["nodes"], list)
                and "edges" in data
                and isinstance(data["edges"], list)
            ):
                valid_nodes = all(
                    isinstance(n, dict) and "id" in n and "label" in n for n in data["nodes"]
                )
                valid_edges = all(
                    isinstance(e, dict) and "from" in e and "to" in e for e in data["edges"]
                )
                if valid_nodes and valid_edges:
                    return data
            print("Groq mindmap output failed validation, falling back to mock")
        except Exception as e:
            print(f"Groq API mindmap generation failed, falling back to mock: {e}")

    return _fallback_mindmap()
