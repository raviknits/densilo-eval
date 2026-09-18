"""Benchmark-only wire observer: record every upstream attempt, never headers."""
import contextvars
import hashlib
import json
import time
import httpx

case_id=contextvars.ContextVar('contextbench_case',default='unattributed')


def install_observer(path):
    original=httpx.AsyncHTTPTransport.handle_async_request
    def write(record):
        with open(path,'a') as out:out.write(json.dumps(record,separators=(',',':'))+'\n')
    class Tee(httpx.AsyncByteStream):
        def __init__(self,stream,record):self.stream=stream;self.record=record;self.data=bytearray();self.start=time.perf_counter()-record.get('headers_s',0);self.closed=False
        async def __aiter__(self):
            try:
                async for chunk in self.stream:
                    if 'first_byte_s' not in self.record:self.record['first_byte_s']=time.perf_counter()-self.start
                    if len(self.data)<20_000_000:self.data.extend(chunk)
                    yield chunk
            finally:await self.finish()
        async def finish(self):
            if self.closed:return
            self.closed=True;usage=None;completed=False;events=[]
            raw=self.data.decode('utf-8',errors='replace')
            for line in raw.splitlines():
                if line.startswith('data: '):
                    try:events.append(json.loads(line[6:]))
                    except ValueError:pass
            if not events:
                try:events=[json.loads(raw)]
                except ValueError:pass
            for event in events:
                if not isinstance(event,dict):continue
                obj=event.get('response',event)
                if isinstance(obj,dict) and isinstance(obj.get('usage'),dict):usage=obj['usage']
                if event.get('type')=='response.completed' or obj.get('status')=='completed':completed=True
            visible=[]
            for event in events:
                if isinstance(event,dict) and event.get('type')=='response.output_item.done':
                    item=event.get('item',{})
                    if item.get('type')=='message':visible.extend(c.get('text','') for c in item.get('content',[]) if c.get('type')=='output_text')
            self.record['visible_output']=''.join(visible)
            if usage:
                # Keep numerical counters, never the provider's identifiers or attribution IDs.
                cleaned={k:v for k,v in usage.items() if isinstance(v,(int,float))}
                for key in ['input_tokens_details','output_tokens_details','prompt_tokens_details','completion_tokens_details']:
                    if isinstance(usage.get(key),dict):cleaned[key]={k:v for k,v in usage[key].items() if isinstance(v,(int,float))}
                self.record['usage']=cleaned
            else:self.record['usage']=None
            self.record.update({'completed_event':completed,'duration_s':time.perf_counter()-self.start,'response_bytes':len(self.data)})
            write(self.record)
        async def aclose(self):
            await self.stream.aclose();await self.finish()
    async def wrapped(self,request):
        if not any(x in request.url.path for x in ['/responses','/messages','/chat/completions']):return await original(self,request)
        try:body=json.loads(request.content)
        except (ValueError,httpx.RequestNotRead):body={}
        record={'case':case_id.get(),'started':time.time(),'path':request.url.path,'host':request.url.host,'request_sha256':hashlib.sha256(request.content).hexdigest(),'body':body}
        tick=time.perf_counter()
        try:response=await original(self,request)
        except Exception as error:
            record.update({'status':None,'usage':None,'error_type':type(error).__name__});write(record);raise
        record['headers_s']=time.perf_counter()-tick
        record['status']=response.status_code;response.stream=Tee(response.stream,record)
        return response
    httpx.AsyncHTTPTransport.handle_async_request=wrapped
