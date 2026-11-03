"""Capture live public official pages without modifying their DOM or content."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent/'browser_capture'
PAGES=[
 ('openai_mini','https://developers.openai.com/api/docs/models/gpt-5.4-mini'),
 ('openai_gpt54','https://developers.openai.com/api/docs/models/gpt-5.4'),
 ('anthropic','https://platform.claude.com/docs/en/about-claude/pricing'),
 ('google','https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash')]

def main():
 OUT.mkdir(exist_ok=True)
 manifest=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
  context=browser.new_context(viewport={'width':1440,'height':1100},locale='en-US')
  for name,url in PAGES:
   page=context.new_page()
   response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
   assert response and response.status==200,(name,response.status if response else None)
   page.locator('body').wait_for(state='visible')
   body=page.locator('body').inner_text()
   assert len(body)>1000,(name,body[:100])
   (OUT/f'{name}.html').write_text(page.content(),encoding='utf-8')
   (OUT/f'{name}.txt').write_text(body,encoding='utf-8')
   targets=[]
   if name.startswith('openai'):
    targets=[('pricing',page.get_by_text('Pricing',exact=True).last)]
   elif name=='anthropic':
    for model,label in [('Claude Opus 5','opus'),('Claude Haiku 4.5','haiku')]:
     rows=page.locator('tr').filter(has_text=model)
     print(name,model,'rows',rows.count(),flush=True)
     targets.append((label,rows.first))
   else:
    headings=page.get_by_role('heading').filter(has_text='Gemini 3.8 Flash')
    print('google matching headings',headings.all_text_contents(),flush=True)
    targets=[('flash38',headings.first)]
   screenshots=[]
   for label,target in targets:
    target.scroll_into_view_if_needed(timeout=15000)
    path=OUT/f'{name}_{label}.png'
    page.screenshot(path=str(path),full_page=False)
    screenshots.append(path.name)
   page.screenshot(path=str(OUT/f'{name}_full.png'),full_page=True)
   screenshots.append(f'{name}_full.png')
   now=datetime.now(timezone.utc)
   files=[f'{name}.html',f'{name}.txt',*screenshots]
   manifest.append(dict(requested_url=url,final_url=page.url,title=page.title(),http_status=response.status,
    retrieved_at_utc=now.isoformat(),retrieved_at_europe_berlin=now.astimezone(ZoneInfo('Europe/Berlin')).isoformat(),
    browser=browser.version,method='Live official HTTPS page rendered by headless Microsoft Edge through Playwright; isolated unauthenticated context; DOM/content unmodified.',
    files={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files}))
   print(name,'captured',screenshots,flush=True)
   page.close()
  browser.close()
 with (OUT/'capture_manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2)

if __name__=='__main__':main()
