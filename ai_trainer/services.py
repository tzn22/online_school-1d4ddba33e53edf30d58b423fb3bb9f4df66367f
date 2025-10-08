import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import OpenAI; if not available, service will raise at runtime.
try:
    import openai
    OPENAI_AVAILABLE = True
    openai.api_key = getattr(settings, "OPENAI_API_KEY", None)
except Exception:
    OPENAI_AVAILABLE = False


class AITrainerService:
    """
    Обёртка для LLM — генерация вопросов и оценка ответов.
    Настройки модели можно положить в settings: AI_TRAINER_MODEL.
    """
    MODEL = getattr(settings, "AI_TRAINER_MODEL", "gpt-4o-mini")

    @classmethod
    def _call_llm(cls, prompt: str, temperature: float = 0.6, max_tokens: int = 1200) -> str:
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI client is not installed/configured (openai package or OPENAI_API_KEY missing).")

        try:
            resp = openai.ChatCompletion.create(
                model=cls.MODEL,
                messages=[
                    {"role": "system", "content": "You are an English teacher and evaluator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content
            return text
        except Exception as e:
            logger.exception("LLM call failed")
            raise

    @classmethod
    def generate_questions(cls, level: str = 'intermediate', count: int = 5):
        """
        Запрос к LLM, возвращаем список объектов: [{"id":1,"question":"..."}...]
        Если LLM вернёт невалидный JSON — попытка fallback парсинга.
        """
        prompt = (
            f"Produce {count} short diverse English test questions for a {level} learner. "
            "Include grammar, vocabulary, reading comprehension and a short speaking prompt. "
            "Return strictly a JSON array of objects with fields: id (int) and question (string)."
        )

        text = cls._call_llm(prompt, temperature=0.7)
        try:
            questions = json.loads(text)
            # validate minimal shape
            if isinstance(questions, list):
                return questions
        except Exception:
            # fallback parse plain lines
            lines = [l.strip('- ').strip() for l in text.splitlines() if l.strip()]
            questions = []
            for i, line in enumerate(lines[:count], start=1):
                questions.append({"id": i, "question": line})
            return questions

    @classmethod
    def evaluate_answers(cls, questions: list, answers: dict):
        """
        Вопросы - list of {id, question}. answers - dict id->text.
        Возвращает словарь:
          { "per_answer": { "1": {"score":8,"feedback":"..."} }, "overall_level": "B1", "summary": "..." }
        """
        qa_texts = []
        for q in questions:
            qid = str(q.get("id"))
            qtext = q.get("question", "")
            ans = answers.get(qid) or answers.get(int(qid)) or ""
            qa_texts.append(f"Q: {qtext}\nA: {ans}")

        joined = "\n\n".join(qa_texts)
        prompt = (
            "You are an experienced English teacher. For each provided Q/A pair, "
            "give a decision correct or incorrect, and a one-sentence feedback assessing grammar, vocabulary and fluency. "
            "Then provide an overall CEFR level (A1..C2) and a short summary with 2-3 recommendations. "
            "Return a valid JSON object like:\n"
            "{\n"
            "  \"per_answer\": {\"1\": {\"score\": 8, \"feedback\": \"...\"}, ...},\n"
            "  \"overall_level\": \"B1\",\n"
            "  \"summary\": \"...\"\n"
            "}\n\n"
            f"Here are the pairs:\n\n{joined}\n"
        )

        text = cls._call_llm(prompt, temperature=0.5)
        try:
            result = json.loads(text)
            return result
        except Exception:
            # fallback: return raw text in 'raw' key so frontend can display
            return {"raw": text}
