import asyncio, json, os, shutil, subprocess, time, urllib.request
from pathlib import Path
os.environ.update(HERMES_HOME='/opt/data', HOME='/opt/data', API_SERVER_ENABLED='true', API_SERVER_HOST='0.0.0.0', API_SERVER_KEY='validation-only-not-a-real-secret', OPENROUTER_API_KEY='validation-only-not-a-real-secret')
Path('/opt/data/workspace').mkdir(parents=True, exist_ok=True)
for name in ['config.yaml', 'SOUL.md']:
 shutil.copy('/etc/oscar/'+name, '/opt/data/'+name)
from hermes_cli.tools_config import _get_platform_tools
from hermes_cli.config import load_config
assert _get_platform_tools(load_config(), 'api_server') == {'oscar'}
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def check_tools():
 async with stdio_client(StdioServerParameters(command='/opt/hermes/.venv/bin/python',args=['/etc/oscar/oscar_tools.py'])) as (read,write):
  async with ClientSession(read,write) as session:
   await session.initialize()
   names=[x.name for x in (await session.list_tools()).tools]
   assert set(names)=={'oscar_get_status','oscar_get_availability','oscar_web_search','oscar_list_vms','oscar_vm_power','oscar_create_vm','oscar_restart_workload','oscar_list_workloads','oscar_scale_workload','oscar_argocd_list_applications','oscar_argocd_sync_application','oscar_ha_get_state','oscar_ha_list_entities','oscar_ha_call_service','oscar_led_get_state','oscar_led_set_state','oscar_led_power','oscar_forgejo_list_repositories','oscar_forgejo_list_pull_requests','oscar_forgejo_read_file','oscar_forgejo_create_branch','oscar_forgejo_write_file','oscar_forgejo_create_pull_request'}, names
   print('MCP_TOOLS',names,flush=True)
   for name,args in [('oscar_get_status',{}),('oscar_get_availability',{'window':'24h'}),('oscar_web_search',{'query_text':'Hermes Agent Nous Research'})]:
    result=await session.call_tool(name,args)
    assert not result.is_error, str(result)
    payload=json.loads(result.content[0].text)
    if name=='oscar_get_status':
     print('LIVE_STATUS', {k: {'status':v['status'],'series':len(v['series'])} for k,v in payload['sources'].items()},flush=True)
    else:
     print('LIVE_TOOL',name,payload.get('status'), 'results',len(payload.get('results',payload.get('success_percent',[]))),flush=True)
asyncio.run(check_tools())
p=subprocess.Popen(['/opt/hermes/.venv/bin/hermes','gateway','run','--no-supervise','--external-supervisor'],stdout=open('/tmp/gateway.log','w'),stderr=subprocess.STDOUT)
try:
 for attempt in range(75):
  if p.poll() is not None: raise RuntimeError('Gateway exited '+str(p.returncode))
  try:
   r=urllib.request.urlopen('http://127.0.0.1:8642/health',timeout=2)
   print('HEALTH',r.status,flush=True)
   req=urllib.request.Request('http://127.0.0.1:8642/v1/models',headers={'Authorization':'Bearer validation-only-not-a-real-secret'})
   print('MODELS',urllib.request.urlopen(req,timeout=3).status,flush=True)
   break
  except OSError: time.sleep(1)
 else: raise RuntimeError('Gateway startup timed out')
finally:
 p.terminate()
 try:p.wait(timeout=20)
 except subprocess.TimeoutExpired:p.kill();p.wait()
 print('GATEWAY_LOG',Path('/tmp/gateway.log').read_text()[-7000:],flush=True)
