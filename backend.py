import ollama
from prompt import study_prompt

def generate_study_response(context_text, user_question):
    """
    Generator that yields tokens from Ollama
    """

    prompt = study_prompt(context_text, user_question)

    stream = ollama.generate(
        model="llama3.2:1b",
        prompt=prompt,
        stream=True,
    )

    for chunk in stream:
        if "response" in chunk:
            yield chunk["response"]
    
    # No changes needed here - backend remains the same