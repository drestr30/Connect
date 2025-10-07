import os
import db_operations as db
import logging
from openai import AzureOpenAI
import json
from dotenv import load_dotenv
import traceback
import db_operations as db
import re

logging.basicConfig(level=logging.INFO)
load_dotenv()

def connect_llm():
    """
    Connects to the Azure OpenAI service using the provided endpoint, model name, and subscription key.
    
    Returns:
        client (AzureOpenAI): An instance of the AzureOpenAI client.
    """
    client = AzureOpenAI(
        api_version=os.environ['LLM_API_VERSION'],
        azure_endpoint=os.environ['LLM_ENDPOINT'],
        api_key=os.environ['LLM_KEY'],
    )
    return client


def call_llm(system_message, user_message, temperature=0.2):
    """
    Calls the Azure OpenAI service to generate a chat completion based on a user query.
    
    Returns:
        response (dict): The response from the Azure OpenAI service containing the chat completion.
    """
    client = connect_llm()
    
    # Create a chat completion request

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            }
        ],
        max_tokens=1024,
        temperature=temperature,
        model=os.environ['LLM_DEPLOYMENT'],
    )
    return response.choices[0].message.content

def format_llm_list_response(agent_response: str) -> list:
    """
    Format the response from an LLM to return a valid json object.
    """
    # Try to extract a JSON object using regex (looking for [...])
    # This regex finds the outermost JSON array by matching the first '[' and the last ']'
    match = re.search(r'(\[.*\])', agent_response, re.DOTALL)
    if match:
        try:
            print(f"group 1: {match.group(1)}")  # Debugging line to see the matched JSON
            response = json.loads(match.group(1))
            return response
        except json.JSONDecodeError as e:
            print(traceback.format_exc())
            print(f"JSON decoding error: {e}")
            response = []
            pass  # If parsing fails, fall through to return text

    # If no JSON object found or parsing fails, return as text
    return response

def format_llm_response(agent_response: str) -> str:
    """
    Format the response from an LLM to return a valid json object.
    """
    # Try to extract a JSON object using regex (looking for {...})
    # This regex finds the outermost JSON object by matching the first '{' and the last '}'
    match = re.search(r'(\{.*\})', agent_response, re.DOTALL)
    if match:
        try:
            print(f"group 1: {match.group(1)}")  # Debugging line to see the matched JSON
            response = json.loads(match.group(1))
            return response
        except json.JSONDecodeError as e:
            print(traceback.format_exc())
            print(f"JSON decoding error: {e}")
            response = {}
            pass  # If parsing fails, fall through to return text

    # If no JSON object found or parsing fails, return as text
    return response

def format_prompt_templates(selections: dict) -> str:
    base_dynamic_template = db.get_prompt_templates("base", selections.get("dynamic"))[0]['prompt']

    default_user_message = f"""
    Given the following user selections: {selections}, generate a unique combination of 10 items that best match these preferences.
    Ensure that the combination is diverse and covers different aspects of the user's interests.
    Provide the output in JSON format as a list of items, where each item includes an 'id' and 'description'.
    """

    system_guidelines = """### Guidelines:  
    - Give your answer in Spanish. 
    - give you answer in JSON format as a list of items, where each item includes an 'id' and 'description'.  
    Use the provided selection to customize your response:"""

    system_message = base_dynamic_template.format(**selections) + system_guidelines
    prompt_templates = []
    for key, value in selections.items():
        if key == "dynamic":
            continue
        try:
            templates = db.get_prompt_templates(key, value)
            prompt_templates.extend(templates)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f"Error fetching session prompts: {e}")
            continue

    logging.info(f"Retrieved {len(prompt_templates)} prompt templates based on selections.")

    if prompt_templates:
        user_message = "\n\n".join([template['prompt'] for template in prompt_templates])
    else:
        user_message = default_user_message

    return system_message, user_message

def generate_session_cards(selections: dict) -> list:
    try:
        system_message, user_message = format_prompt_templates(selections)
        response = call_llm(system_message, user_message)
        logging.info(f"LLM response: {response}")
        formatted_response = format_llm_list_response(response)
 
        return formatted_response
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(f"Error generating session cards: {e}")
        return []
    
if __name__ == "__main__":
    
        test_selections = {     
            "social_context": "friends",
            "purpose": "meet",
            "tone": "2"
        }
        cards = generate_session_cards(test_selections)
        print(cards)