# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-class-docstring

from __future__ import annotations
import typing
import logging
import requests
import json
import re
import markdown2


from flask_babel import gettext
from urllib.parse import quote
from searx.result_types import EngineResults
from searx import settings
from babel import Locale
from searx.plugins import Plugin, PluginInfo


if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg

logger = logging.getLogger(__name__)


system_prompt = """
You are a helpful assistant named Super Paco. Your task is to provide an informative, concise, and structured response to the user's query.

Respond using **key-value pairs**, in the **exact format** shown below. The response must be in **plain text** with **no Markdown**, and **only use simple HTML** (like <br>, <b>, <i>, <p>, <ul>, <li>) inside the Explanation field.

Format your response like this:

Topic: [short title of the topic]
Explanation: [detailed explanation in about 300 words, using simple HTML for readability — for example, wrap paragraphs in <p>...</p> or use <ul><li>...</li></ul> for short lists]
Key Facts: [comma-separated list of 3–6 important facts]
Useful For: [list who or what this topic is useful for]
Example: [one short real-world example]

Only include the fields that are relevant to the query. Do NOT include any headings, bullet points, or extra formatting outside the specified structure.

Always reply in the language of the user's question.
"""

system_prompt_template = """
You are a helpful assistant named Super Paco. Your task is to provide a clear, informative, and well-structured answer to the user's query using Markdown formatting.

Guidelines:
    - Clarity: Use bullet points or lists for easy readability.
    - Conciseness: Provide essential information without unnecessary detail.
    - Sources: Include links to relevant sources for further reading.
    - Structure: Organize information logically with headings and subheadings.

Respond in Markdown, using appropriate elements such as:
- **Headings** (`#`, `##`, etc.)
- **Paragraphs**
- **Bold** for emphasis
- **Lists** (ordered or unordered)
- **Code blocks** (if relevant)
- **Links** (if needed)

Always reply in the same language the user used in their question.
If you cannot detect the language, here is the language from user settings: {language_name}
"""


class SXNGPlugin(Plugin):
    """Simple plugin that displays information from openwebui AI intent based agent.
    The information is displayed in area for the
    "answers".
    """
    id = "ai_overview"
    default_on = False

    def __init__(self, plg_cfg: "PluginCfg"):
        super().__init__(plg_cfg)
        

        self.info = PluginInfo(
            id=self.id,
            name=gettext("AI Overview"),
            description=gettext("Displays an AI-generated overview at the top of search results."),
            examples=["How does photosynthesis work?", "What is quantum computing?"],
            preference_section="general",
        )

        config = settings.get("ai_overview", {})
        self.api_key = config.get("openai_key", "")
        self.sng_token = config.get("sng_token", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 500)
        self.ai_url = config.get("ai_url", "")
        self.timeout = config.get("timeout", 60)
        #self.ai_token = 'ODg5OWZlZjkxNjYyZDk4YjhjZjZjMjg1'

    def parse_infobox(self, text: str) -> list[tuple[str, str]]:
       lines = text.strip().splitlines()
       pairs = []
       for line in lines:
           if ":" in line:
               key, value = line.split(":", 1)
               pairs.append((key.strip(), value.strip()))
       return pairs


    def is_authorized(self, request: SXNG_Request) -> bool:
        user_tokens = request.preferences.tokens.values or {}
        # get_value returns the actual value (dict expected for 'tokens')
        #print(f"User tokens: {user_tokens}") 
        #print("Tokens (actual values):", request.preferences.tokens.values)
        return self.sng_token in user_tokens
    

    def call_openai(self, request: SXNG_Request, query: str) -> str | None:
        response = None
        try:
            headers = {
                "Authorization": f"Bearer {quote(self.api_key)}",
                "Content-Type": "application/json",
            }
            lang_code = request.preferences.get_value("language") or "en"

            if lang_code in (None, "", "auto", "default", "system"):
                lang_code = "en"
            
            try:
                locale = Locale.parse(lang_code)
            except Exception:
                # Fallback if the code is still invalid (e.g. "en-US-extra")
                locale = Locale.parse("en")


            language_name = locale.get_display_name() # Returns 'English' or localized name
            
            print(f"Language name: {language_name}")
            system_prompt = system_prompt_template.format(language_name=language_name)
            #[AI Overview] Unexpected error: unknown locale 'auto' | Response: No response

            chat_log = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query}]
            payload = {
                "model": self.model,
                'messages': [{'role': msg['role'], 'content': msg['content']} for msg in chat_log],
                "temperature": 0.7,
                "max_tokens": self.max_tokens,
                'stream': False,
            }

            response = requests.post(
                self.ai_url,
                headers=headers,
                json=payload,
                timeout=100,
            )
            response.raise_for_status()
            resp = response.json()

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
            err_text = response.text if response else "No response"
            logger.error(f"[AI Overview] HTTP error: {http_err} | Response: {err_text}")
            return f"HTTP error occurred: {http_err}"

        except Exception as e:
            err_text = response.text if response else "No response"
            logger.error(f"[AI Overview] Unexpected error: {str(e)} | Response: {err_text}")
            return f"[AI Overview] Unexpected error: {str(e)} | Response: {err_text}"

    def post_search(self, request: SXNG_Request, search: SearchWithPlugins) -> EngineResults:
        results = EngineResults()

        if search.search_query.pageno > 1 or not self.is_authorized(request):
            ai_answer_a = f"Set in general preferences engine tokens"
            results.add(results.types.Answer(answer=ai_answer_a.strip()))
            return results
            

        query = search.search_query.query.strip()
        
        if not query:
            ai_answer_a = "Please enter a query and remember to include 'ai' at the end for AI assistance."
            results.add(results.types.Answer(answer=ai_answer_a.strip()))
            return results
        if query.casefold().endswith(" ai"):
            query = query[:-3].rstrip()
        else:
            ai_answer_a = f"If you want to get an answer from AI, please include AI at the end of query."
            results.add(results.types.Answer(answer=ai_answer_a.strip()))
            return results
    
        ai_answer = self.call_openai(request,query)
        if ai_answer:
            answer_html = markdown2.markdown(ai_answer)
            results.add(results.types.Answer(answer=answer_html))
 
   #             parsed = self.parse_infobox(ai_answer) 
   #             if parsed:
   #                 attributes = [{"label": k, "value": v} for k, v in parsed]
   #                 infobox = {
   #                     "infobox": "AI Overview",
   #                     "content": "",  # optional or you can choose one field as summary
   #                     "attributes": attributes,
   #                     "urls": []
   #                 }
   #                 results.add(infobox)
   #                 
   #             else:
   #                 results.add(results.types.Answer(answer=ai_answer.strip()))
   #                 


        return results
