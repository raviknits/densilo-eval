"""Launch full product proxies in separate preinstalled environments."""
import argparse,importlib.util,importlib.metadata,json
from pathlib import Path
from .observer import install_observer,case_id

class CaseMiddleware:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  token=case_id.set(dict(scope.get('headers',[])).get(b'x-contextbench-case',b'unattributed').decode())
  try:await self.app(scope,receive,send)
  finally:case_id.reset(token)

def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',required=True,choices=['native','candidate','headroom_cache','headroom_token','headroom_lossless']);p.add_argument('--port',required=True,type=int);p.add_argument('--evidence',required=True);a=p.parse_args()
 root=Path(a.evidence);root.mkdir(parents=True,exist_ok=True);install_observer(root/'upstream.jsonl')
 if a.arm in ('native','candidate'):
  if importlib.util.find_spec('headroom') is not None:raise RuntimeError('Use an isolated Densilo environment without Headroom')
  from contextbench.standalone.server import Config,create_app
  app=create_app(Config(optimize=a.arm=='candidate'));version=importlib.metadata.version('densilo-gateway')
 else:
  from headroom.proxy.models import ProxyConfig
  from headroom.proxy.server import create_app
  version=importlib.metadata.version('headroom-ai')
  if version!='0.37.0':raise RuntimeError('Baseline is pinned to Headroom 0.37.0; preregister changes')
  app=create_app(ProxyConfig(host='127.0.0.1',port=a.port,mode='token' if a.arm=='headroom_token' else 'cache',lossless=a.arm=='headroom_lossless',memory_enabled=False))
 app.add_middleware(CaseMiddleware)
 (root/'launch.json').write_text(json.dumps({'arm':a.arm,'version':version,'port':a.port,'scope':'full proxy; optional enterprise/learning/image paths evaluated separately'},indent=2)+'\n')
 import uvicorn
 uvicorn.run(app,host='127.0.0.1',port=a.port,access_log=False)

if __name__=='__main__':main()
