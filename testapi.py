import google.generativeai as genai
from google.generativeai import types
import os

# --- IMPORTANT ---
# Replace "YOUR_API_KEY" with your actual Google AI Studio API key.
# You can also store it as an environment variable (e.g., GOOGLE_API_KEY) for better security.
# For example: genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


def query_gemini(prompt_text):
    """
    Sends a prompt to the Gemini Pro API and returns the generated text.

    Args:
        prompt_text: The text prompt to send to the model.

    Returns:
        A string containing the model's response, or an error message.
    """
    try:
        # Configure the library with your API key
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

        # Create an instance of the GenerativeModel for 'gemini-pro'
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Send the prompt to the model to generate content
        print("Sending prompt to Gemini...")
        response = model.generate_content(prompt_text)


        # need to add logic to disable thinking for faster inference thinking is enabled by default

        # The response object contains the generated text in the .text attribute.
        # It also has other useful properties like `prompt_feedback` for safety ratings.
        return response.text

    except Exception as e:
        # Handle potential exceptions, such as authentication errors or network issues.
        return f"An error occurred: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    # 1. Define the prompt you want to send to the model.
    user_prompt = "Explain the concept of quantum entanglement in ONE LINE."

    # 2. Call the function with your prompt.
    gemini_response = query_gemini(user_prompt)

    # 3. Print the result.
    print("\n--- Gemini's Response ---")
    print(gemini_response)
    print("-------------------------\n")

