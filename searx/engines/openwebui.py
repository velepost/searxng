# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# show on /usr/local/new_searxng_docker/git_searx/searx/templates/simple/elements/infobox.html
"""
Chat GPT Openwebui
"""
import json
import re
import requests
from urllib.parse import quote
import uuid
import markdown2

# About information
about = {
    "website": 'https://openwebui.myvelecloud.com/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}
API_KEY = ""  # Set your API key here
OPEN_AI_URL = ""
GPT_MODEL = ""  # Set your model name, if applicable
IBOX_TITLE = ""  # Set the title for the infobox
OPEN_AI_URL_LOCAL = ""

def send_request(query: str, chat_log=None):
    """
    Sends a chat request to the API endpoint.

    Parameters
    ----------
    query : str
        The user's query to be sent to the chat model.
    chat_log : list, optional
        The conversation history for the chat session.

    Returns
    -------
    str
        The response from the chat model.

    Raises
    ------
    Exception
        For handling errors during the API request.
    """
    gpt_title = 'AI assistant' if not IBOX_TITLE else IBOX_TITLE
    model_name = 'crawl4ai_pipeline' if not GPT_MODEL else GPT_MODEL
    gpt_temp=0.7 if not GPT_TEMPERATURE else GPT_TEMPERATURE
    max_tok=500 if not MAX_TOKENS else MAX_TOKENS

    if query.casefold().endswith(" gpt"):
        query = query[:-4].rstrip()
    else:
        return f"> If you want to get an answer from {str(gpt_title)}, please include GPT at the end of query.<br>GPT Model: {str(model_name)}"


    chat_log = [{'role': 'user', 'content': query}]


    # Prepare the payload for the API request
    payload = {
        'model': model_name,
        'temperature': gpt_temp, 
        'max_tokens': max_tok,
        'stream': False,
        'messages': [{'role': msg['role'], 'content': msg['content']} for msg in chat_log],
    }
    
    # Prepare the headers for the request
    headers = {
        'Authorization': f'Bearer {quote(API_KEY)}',
        'Content-Type': 'application/json'
    }
    
    # Debug print the headers
    #print("Headers:", headers)
    # Debug print the payload
    #print("Payload:", json.dumps(payload, indent=2))  # Pretty print the JSON payload
    try:
        # Send the POST request to the API endpoint
        response = requests.post(OPEN_AI_URL, headers=headers, json=payload)
        print(f"Response text 1: {response.text}")
        response.raise_for_status()  # Raise an exception for HTTP error responses
        resp = response.json()
        # Extract the assistant's answer from the response structure
       
        if "choices" in resp and len(resp["choices"]) > 0:
        # Access the first choice
            message = resp["choices"][0].get('message', {})
            answer = message.get('content', '')  # Get the content of the message
            return answer
        else:
            answer = ''  # No choices available
        
        messages = resp.get('messages', [])
        if messages:
            for msg in messages:
                if msg['role'] == 'assistant':
                    answer = msg['content']
                    break
        return answer

    except requests.exceptions.HTTPError as http_err:
        print(f"Response text 2: {response.text} error: {http_err}")
        return f"HTTP error occurred: {http_err}"
    except Exception as e:
        print(f"Response text 3: {response.text} error: {str(e)}")
        return f"Request error: {str(e)}"



def request(query, params):
    """Build request."""
    # Fake request for now
    params['query'] = query
    params['url'] = "https://www.google.com"
    params['engine_data']['token'] = "aaaa"
    return params

def response(resp):
    """Parse response."""
    gpt_title = IBOX_TITLE
    try:
        content = send_request(resp.search_params['query'])
    except Exception as e:
        content = f"Response error: {str(e)}"
        
    answer_html = markdown2.markdown(content)
    urls = []
    if 'OPEN_AI_URL_LOCAL' in globals():
        urls.append({'title': str(gpt_title), 'url': OPEN_AI_URL_LOCAL})


    results = [
        {
            'infobox': gpt_title,
            'content': answer_html,
            'urls': urls,
        }
    ]
    return results