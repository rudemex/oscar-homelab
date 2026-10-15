import json,os,secrets,subprocess,time,urllib.request,urllib.error
from pathlib import Path
password=secrets.token_urlsafe(30)
os.environ.update(HOME='/app/backend/data',STATIC_DIR='/app/backend/data/static',ENABLE_TITLE_GENERATION='false',ENABLE_TAGS_GENERATION='false',ENABLE_FOLLOW_UP_GENERATION='false',CORS_ALLOW_ORIGIN='http://localhost:8080',WEBUI_ADMIN_EMAIL='admin@oscar.home',WEBUI_ADMIN_PASSWORD=password,WEBUI_SECRET_KEY=secrets.token_urlsafe(32),ENABLE_SIGNUP='false',WEBUI_AUTH='true',ENABLE_OLLAMA_API='false',OPENAI_API_BASE_URL='http://127.0.0.1:9/v1',OPENAI_API_KEY='validation-only',OFFLINE_MODE='true',HF_HUB_OFFLINE='1',ENABLE_VERSION_UPDATE_CHECK='false',ENABLE_DIRECT_CONNECTIONS='false',ENABLE_CODE_EXECUTION='false',ENABLE_CODE_INTERPRETER='false',ENABLE_EVALUATION_ARENA_MODELS='false',ENABLE_COMMUNITY_SHARING='false',ENABLE_PERSISTENT_CONFIG='false')
p=subprocess.Popen(['bash','start.sh'],cwd='/app/backend',stdout=open('/tmp/webui.log','w'),stderr=subprocess.STDOUT)
try:
 for _ in range(180):
  if p.poll() is not None: raise RuntimeError('WebUI exited '+str(p.returncode))
  try:
   r=urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2)
   print('WEBUI_HEALTH',r.status,flush=True)
   break
  except OSError:time.sleep(1)
 else:raise RuntimeError('WebUI timeout')
 req=urllib.request.Request('http://127.0.0.1:8080/api/v1/auths/signin',data=json.dumps({'email':'admin@oscar.home','password':password}).encode(),headers={'Content-Type':'application/json'})
 auth=json.load(urllib.request.urlopen(req,timeout=10))
 assert auth['role']=='admin'
 print('ADMIN_SIGNIN_OK',flush=True)
 req=urllib.request.Request('http://127.0.0.1:8080/api/v1/auths/signup',data=json.dumps({'name':'test','email':'test@oscar.home','password':password}).encode(),headers={'Content-Type':'application/json'})
 try:
  urllib.request.urlopen(req,timeout=10)
  raise RuntimeError('Signup unexpectedly accepted')
 except urllib.error.HTTPError as e:
  assert e.code in [401,403],e.code
  print('SIGNUP_BLOCKED',e.code,flush=True)
finally:
 p.terminate()
 try:p.wait(timeout=15)
 except subprocess.TimeoutExpired:p.kill();p.wait()
 log=Path('/tmp/webui.log').read_text()
 print('LOG_LAST_LINES',log[-6000:].replace(password,'[REDACTED]'),flush=True)
