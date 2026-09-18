"""Direct Responses transport. Credentials never enter traces or tool workers."""
import json
import os
from pathlib import Path
import httpx


class ProviderError(RuntimeError):
    pass


class ResponsesProvider:
    def __init__(self, model, auth='api'):
        self.model=model;self.auth=auth
        if auth=='api':
            key=os.environ.get('OPENAI_API_KEY')
            if not key:raise ProviderError('OPENAI_API_KEY is required for api auth')
            self.url='https://api.openai.com/v1/responses';self.headers={'Authorization':'Bearer '+key}
        elif auth=='codex':
            # Explicit opt-in experimental transport, used only for local subscription tests.
            d=json.loads((Path.home()/'.codex/auth.json').read_text());t=d['tokens']
            self.url='https://chatgpt.com/backend-api/codex/responses'
            self.headers={'Authorization':'Bearer '+t['access_token'],'ChatGPT-Account-ID':t['account_id'],'originator':'codex_cli_rs','OpenAI-Beta':'responses=experimental'}
        else:raise ValueError('Unknown auth mode')
        self.client=httpx.Client(timeout=90,trust_env=False)

    def call(self, instructions, messages, tools):
        body={'model':self.model,'instructions':instructions,'input':messages,'tools':tools,'stream':True,'store':False,'reasoning':{'effort':'low'},'parallel_tool_calls':False}
        result=None;items={}
        with self.client.stream('POST',self.url,headers=self.headers,json=body) as r:
            if r.status_code!=200:
                # Server messages can reflect input: generated fixtures only; never headers.
                raise ProviderError(f'HTTP {r.status_code}: '+r.read().decode()[:300])
            for line in r.iter_lines():
                if not line.startswith('data: '):continue
                try:event=json.loads(line[6:])
                except json.JSONDecodeError:continue
                if event.get('type')=='response.output_item.done':items[event.get('output_index',len(items))]=event['item']
                if event.get('type') in ['response.completed','response.incomplete']:result=event['response']
                if event.get('type') in ['response.failed','error']:raise ProviderError(str(event.get('error',event.get('response',{}).get('error','stream failure')))[:300])
        if not result:raise ProviderError('stream ended without terminal response')
        if not result.get('output') and items:result['output']=[items[k] for k in sorted(items)]
        return result

    def close(self):self.client.close()


def usage_of(response):
    u=response.get('usage')
    if not isinstance(u,dict) or any(k not in u for k in ('input_tokens','output_tokens')):return None
    return {'input':u['input_tokens'],'output':u['output_tokens'],'cached_input':u.get('input_tokens_details',{}).get('cached_tokens',0),'reasoning':u.get('output_tokens_details',{}).get('reasoning_tokens',0)}
