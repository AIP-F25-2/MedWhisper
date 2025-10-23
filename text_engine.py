from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load model + tokenizer once (global)
tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
model = AutoModelForCausalLM.from_pretrained("distilgpt2")

def generate_response(user_input: str, max_length: int = 100) -> str:
    """
    Generate a chatbot response from user input using a causal LM.
    """
    # Tokenize input
    inputs = tokenizer.encode(user_input, return_tensors="pt")

    # Generate output tokens
    outputs = model.generate(
        inputs,
        max_length=max_length,
        do_sample=True,        # Random sampling for variety
        top_p=0.95,            # Nucleus sampling
        top_k=50,              # Top-k filtering
        pad_token_id=tokenizer.eos_token_id
    )

    # Decode output tokens
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Remove echo of user input if present
    if response.lower().startswith(user_input.lower()):
        response = response[len(user_input):].strip()

    # Clean response formatting
    return response.strip()
