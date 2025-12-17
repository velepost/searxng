# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# show on /usr/local/new_searxng_docker/git_searx/searxng/searx/templates/simple/elements/infobox.html
"""
Ghat GPT
"""

import json
import re
import requests
from urllib.parse import quote
import uuid
import markdown2
from openai import OpenAI



# about
about = {
    "website": 'https://openwebui.myvelecloud.com/',
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}



API_KEY = ""
OPEN_AI_URL = ""
GPT_MODEL = ""
IBOX_TITLE = ""
OPEN_AI_URL_LOCAL = ""

def send_request(query: str, chat_log=None):
    gpt_title = 'Chat GPT' if not IBOX_TITLE else IBOX_TITLE
    openai_gpt_model = 'gpt-3.5-turbo' if not GPT_MODEL else GPT_MODEL
    gpt_temp=0.7 if not GPT_TEMPERATURE else GPT_TEMPERATURE
    max_tok=200 if not MAX_TOKENS else MAX_TOKENS


    if query.casefold().endswith(" gpt"):
        query = query[:-4].rstrip()
    else:
        return f"> If you want to get an answer from {str(gpt_title)}, please include GPT at the end of query.<br>GPT Model: {str(openai_gpt_model)}"

    
    if chat_log is None:
        chat_log = [{
            'role': 'system',
            'content': f'Your name is {str(gpt_title)}. You are a knowledgeable and informative search engine. Provide clear and concise answers to search queries.',
        }]
    try:
        client = OpenAI(
            api_key = quote(API_KEY)
        )
        chat_log.append({'role': 'user', 'content': query})        
        messages = [{'role': msg['role'], 'content': msg['content']} for msg in chat_log]
        
        resp = client.chat.completions.create(
            model=openai_gpt_model,
            messages=messages,
            temperature=gpt_temp, 
            max_tokens=max_tok,
        )
        
        answer = resp.choices[0].message.content
        #answer_html = markdown2.markdown(answer)
        chat_log.append({'role': 'assistant', 'content': answer})
        return answer   
    except Exception as e:
        # Print or log the actual error details
        return f"{str(gpt_title)} request error: {str(e)}"

    


def request(query, params):
    # todo: the requests are working but the response method is never called
    # todo: we have to cache get_authorization_token()
    """build request"""

    # fake request for now
    params['query'] = query
    params['url'] = "https://www.google.com"
    params['engine_data']['token'] = "aaaa"
    return params




def response(resp):
    """parse response"""
    gpt_title = 'Chat GPT' if not IBOX_TITLE else IBOX_TITLE
    try:
        content = send_request(resp.search_params['query'])
    except Exception as e:
        content = f"{str(gpt_title)} response error: {str(e)}"

    answer_html = markdown2.markdown(content)
    urls = []
    
    if 'OPEN_AI_URL_LOCAL' in globals():
        urls.append({'title': str(gpt_title), 'url': OPEN_AI_URL_LOCAL})
    
    openai_gpt_url = 'https://chat.openai.com' if not OPEN_AI_URL else OPEN_AI_URL
    urls.append({'title': 'ChatGPT', 'url': openai_gpt_url})

    
    results = [
        {
            'infobox': gpt_title,
            'content': answer_html,
            'urls' : urls,
        }
    ]
    return results