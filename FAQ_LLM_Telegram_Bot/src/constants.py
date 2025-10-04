from pathlib import Path

WELCOME_MESSAGE = "Welcome babe"
WAITING_MESSAGE = "bot is thinking..."
MAX_RESPONSE_LENGTH = 5000000000
LLM_MODEL = "gemini-2.5-flash"


SYSTEM_PROMPT = f"""You are a helpful and highly precise assistant for Telegram chats.
- Prioritize correctness, completeness, and clear structure.
- don't repeat the question in your answer.
- don't use italic in your answer.
- dont use emojis in your answer.
- Use Telegram-friendly Markdown: short headings (###), bullet points (-), and fenced code blocks.
- Keep paragraphs short for mobile readability. Use bold for key points sparingly.
- Provide long, thorough answers when needed. If response is very long, add mini table of contents.
- If info is missing, state assumptions briefly.

Use this context to answer the questions
(if the question is not related to this context,
answer with the most accurate and complete response possible):
"""

REPLY_SYSTEM_PROMPT = SYSTEM_PROMPT + """
Answer the following question according to the guideline.
Guideline: {reply_guideline}
"""

# emojis
LIKE_EMOJI = ":thumbs_up:"
DISLIKE_EMOJI = ":thumbs_down:"
BOT_EMOJI = ":moai:"
CRY_EMOJI = ":crying_face:"
QUESTION_EMOJI = ":question:"
HEART_EMOJI = ":red_heart:"
PILE_OF_POO_EMOJI = ":pile_of_poo:"
THINKING_EMOJI = ":thinking_face:"
HIGH_VOLTAGE_EMOJIS = {":high_voltage:", ":zap:"}