import streamlit as st
import google.generativeai as genai
import os
import pandas as pd # Import pandas to handle DataFrame
import re # Import regex for text processing
import google.api_core.exceptions # Import specific exceptions for better error handling

def initialize_gemini_client():
    """
    Initializes the Gemini client using the API key from session state.
    Handles potential errors during initialization.
    """
    api_key = st.session_state.get('GEMINI_API_KEY')

    if not api_key:
        st.error("⚠️ Gemini API key is not set in the settings.")
        return None

    try:
        genai.configure(api_key=api_key)
        # Optional: Test a simple call to check if the key is valid
        # try:
        #     models = genai.list_models()
        #     print("Successfully connected to Gemini API.")
        # except Exception as e:
        #      st.error(f"⚠️ Error connecting to Gemini API with provided key: {e}")
        #      return None

        # Return the generative model object, not the client itself
        # The common usage is to get the model directly after configuring
        model = genai.GenerativeModel('gemini-pro') # Or another suitable model
        return model

    except google.api_core.exceptions.GoogleAPIError as e:
        st.error(f"⚠️ Google API Error during Gemini client initialization: {e}")
        return None
    except Exception as e:
        st.error(f"⚠️ Unexpected Error during Gemini client initialization: {e}")
        return None


def format_ai_response(response_text):
    """
    Formats the raw AI response text for better presentation in Streamlit.
    Adds basic formatting like ensuring paragraphs are separated.
    """
    if not response_text:
        return ""

    # Replace multiple newlines with double newlines to ensure paragraph separation
    formatted_text = re.sub(r'\n{2,}', '\n\n', response_text)

    # Optional: Add more formatting based on expected response structure
    # For example, if expecting lists, you might process lines starting with -, *, or numbers
    # If expecting bolding, you might process text enclosed in **

    return formatted_text


def generate_ai_advice(user_query, gemini_model, historical_data=None):
    """
    Generates AI advice based on the user prompt, historical data, and the Gemini model.
    Processes and formats the response before returning.
    """
    if gemini_model is None:
        st.warning("Gemini client is not initialized. Please set the API key in settings.")
        return "AI assistant is not available."

    prompt_parts = []
    prompt_parts.append("Analyze the following data and provide insights and actionable advice based on the user's question.")

    if historical_data is not None and not historical_data.empty: # Check if data is not None and not empty
        prompt_parts.append("\n\nHistorical Analysis Data:")
        # Convert DataFrame to a string format, e.g., markdown table or string
        # Using to_string() for simplicity, consider to_markdown() for better formatting
        prompt_parts.append(historical_data.to_string(index=False))
    elif historical_data is not None and historical_data.empty:
        prompt_parts.append("\n\nNo historical analysis data available.")


    prompt_parts.append(f"\n\nUser's Question: {user_query}")

    # Add constraints or desired output format, asking for clear paragraphs
    prompt_parts.append("\n\nProvide a concise summary and focus on actionable recommendations based on the available data and the user's question. Ensure the response is formatted with clear paragraph breaks.")


    full_prompt = "\n".join(prompt_parts)

    try:
        # Use the model object to generate content
        response = gemini_model.generate_content(full_prompt)
        # Process and format the raw response text
        formatted_advice = format_ai_response(response.text)
        return formatted_advice
    except google.api_core.exceptions.DeadlineExceeded as e:
        st.error(f"⚠️ The Gemini API request timed out: {e}")
        return "Error: The request to the AI assistant timed out."
    except google.api_core.exceptions.ResourceExhausted as e:
        st.error(f"⚠️ Gemini API rate limit exceeded: {e}")
        return "Error: You have exceeded the rate limit for the AI assistant. Please try again later."
    except google.api_core.exceptions.PermissionDenied as e:
        st.error(f"⚠️ Permission denied for Gemini API. Check your API key and project settings: {e}")
        return "Error: Permission denied. Please check your API key and project settings."
    except google.api_core.exceptions.InvalidArgument as e:
        st.error(f"⚠️ Invalid argument provided to Gemini API: {e}")
        return "Error: Invalid input provided to the AI assistant."
    except google.api_core.exceptions.GoogleAPIError as e:
        st.error(f"⚠️ Google API Error during AI advice generation: {e}")
        return "Error generating advice from AI."
    except Exception as e:
        st.error(f"⚠️ Unexpected Error generating AI advice: {e}")
        return "Error generating advice from AI."

