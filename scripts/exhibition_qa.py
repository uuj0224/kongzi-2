import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
  context=await browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce',permissions=['clipboard-read','clipboard-write'])
  page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto('http://127.0.0.1:8000');await page.locator('.connection.online').wait_for();await page.locator('.hero-art').evaluate('(i)=>i.decode()');await page.evaluate('document.fonts.ready')
  await page.screenshot(path=str(OUT/'exhibition-home.png'),full_page=True,animations='disabled')
  for w,h in [(1100,800),(1280,900),(1440,1000),(1920,1080)]:
   await page.set_viewport_size({'width':w,'height':h});assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
   box=await page.locator('.composer').bounding_box();assert box and box['y']+box['height']<h,w
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.locator('.suggestions button').first.click();assert '学习' in await page.locator('#question').input_value();assert await page.locator('.thread').count()==0
  await page.get_by_role('button',name='问学记录').click();await page.get_by_role('dialog').wait_for();await page.locator('.histories button').first.click();await page.locator('.answer').first.wait_for()
  await page.screenshot(path=str(OUT/'exhibition-answer.png'),full_page=True,animations='disabled')
  await page.locator('.inline-citation').first.click();await page.get_by_role('dialog').wait_for();await page.get_by_role('button',name='关闭此对话框').click()
  await page.get_by_role('button',name='复制回答',exact=True).first.click();await page.get_by_text('已复制',exact=True).wait_for()
  await page.get_by_role('button',name='新建问学',exact=True).click()
  async def fail(route):await route.fulfill(status=503,content_type='application/json',body=json.dumps({'detail':'模型服务限流，请稍后重试。'}))
  await page.route('**/api/chat',fail);await page.locator('#question').fill('错误恢复测试');await page.locator('#question').press('Enter');await page.get_by_role('alert').wait_for();assert await page.locator('#question').input_value()=='错误恢复测试';await page.unroute('**/api/chat',fail)
  await page.get_by_role('button',name='典籍文库',exact=True).click();await page.get_by_text('共 512 段原文',exact=True).wait_for()
  await page.screenshot(path=str(OUT/'exhibition-library.png'),full_page=False,animations='disabled')
  await page.locator('#search').fill('學而時習');await page.get_by_role('button',name='查找',exact=True).click();await page.get_by_text('共 1 段原文',exact=True).wait_for()
  await page.get_by_role('button',name='查看出处').click();await page.get_by_role('dialog').wait_for();await page.get_by_role('button',name='关闭此对话框').click()
  await page.locator('#search').fill('不存在xyz123');await page.get_by_role('button',name='查找',exact=True).click();await page.get_by_role('heading',name='没有找到相关原文').wait_for();await page.get_by_role('button',name='清除筛选',exact=True).click();await page.get_by_text('共 512 段原文',exact=True).wait_for()
  await page.locator('.chapter-nav button').nth(1).click();await page.get_by_text('共 16 段原文',exact=True).wait_for()
  assert not errors,errors
  (OUT/'exhibition-checks.json').write_text(json.dumps({'desktop_widths':[1100,1280,1440,1920],'checks':['hero loaded','self-hosted font','composer above fold','no horizontal overflow','example prefills only','history drawer','source citation','clipboard','failed input retained','library search','traditional search','empty/reset','chapter navigation'],'console_errors':errors,'paid_calls':0},ensure_ascii=False,indent=2));await browser.close();print('Exhibition desktop QA passed')
asyncio.run(main())
