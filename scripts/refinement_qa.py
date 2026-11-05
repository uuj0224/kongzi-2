"""Desktop regression for critique fixes; all model/history requests are intercepted."""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'


async def main():
    OUT.mkdir(exist_ok=True)
    passage = json.loads((ROOT / 'data/passages.json').read_text())[0]
    histories = [
        {'id': str(i), 'title': '如何学习？', 'full_title': '如何学习？' + ('请结合生活解释，保留完整问题。' * 5 if i == 2 else ''),
         'updated_at': f'2026-11-0{i} 08:30:00', 'message_count': i,
         'preview': '温习与实践。' if i == 1 else '将学习与思考结合。'}
        for i in (1, 2)
    ]
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel='chrome', headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page = await context.new_page()
        errors, calls = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.route('**/api/health', lambda route: route.fulfill(json={'model_configured': True, 'index_ready': True, 'passages': 568}))
        await page.route('**/api/conversations', lambda route: route.fulfill(json=histories))

        async def conversation(route):
            answer = ('核心理解：学习需要实践。[' + passage['id'] + ']\n\n原文依据：请核对原文。\n\n现代延伸解读：可以记录学习计划。')
            if route.request.url.endswith('/2'):
                answer = '原文依据不足时，应说明限制。现代延伸解读：可以记录学习计划。需要注意，项目释义不是权威译注。'
            await route.fulfill(json={'messages': [{'id': 1, 'question': '如何学习？', 'answer': answer,
                'citations': [passage], 'candidates': [], 'elapsed_ms': 1000, 'status': 'ok'}]})

        await page.route('**/api/conversations/*', conversation)
        mode = 'fail'

        async def chat(route):
            calls.append(route.request.post_data_json)
            if mode == 'delay':
                await asyncio.sleep(2)
            await route.fulfill(status=503, json={'detail': '模型暂时不可用，请重试。'})

        await page.route('**/api/chat', chat)
        await page.goto('http://127.0.0.1:8000')
        await page.locator('.connection.online').wait_for()
        assert await page.locator('.connection').get_attribute('role') == 'status'
        for width, height in [(1100, 800), (1280, 900), (1440, 1000), (1920, 1080)]:
            await page.set_viewport_size({'width': width, 'height': height})
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            box = await page.locator('.composer').bounding_box()
            assert box and box['y'] + box['height'] < height, width
        await page.set_viewport_size({'width': 1440, 'height': 1000})
        await page.screenshot(path=str(OUT / 'refined-home.png'), full_page=True)

        await page.locator('#question').fill('保留我的草稿')
        await page.locator('.suggestions button').first.click()
        assert (await page.locator('#question').input_value()).startswith('保留我的草稿')
        assert not calls
        draft = await page.locator('#question').input_value()

        async def open_history(index):
            await page.get_by_role('button', name='问学记录').click()
            await page.locator('.history-entry').first.wait_for()
            await page.locator('.histories > button').nth(index).click()
            await page.locator('.answer-section').first.wait_for()

        await page.get_by_role('button', name='问学记录').click()
        await page.locator('.history-entry').first.wait_for()
        assert await page.locator('.history-entry small').count() == 2
        assert await page.locator('.history-preview').count() == 2
        await page.screenshot(path=str(OUT / 'refined-history.png'))
        await page.get_by_role('searchbox', name='搜索问学记录').fill('温习')
        assert await page.locator('.histories > button').count() == 1
        await page.get_by_role('searchbox', name='搜索问学记录').fill('没有这条记录')
        await page.get_by_text('没有匹配的问学记录。', exact=True).wait_for()
        await page.get_by_role('button', name='清除搜索', exact=True).click()
        await page.locator('.histories > button').first.click()
        await page.locator('.answer-section').first.wait_for()
        assert await page.locator('.answer-section').count() == 3
        assert '原文' in await page.locator('.inline-citation').first.get_attribute('aria-label')
        await page.locator('#question').fill('会话一草稿')
        await page.screenshot(path=str(OUT / 'refined-answer.png'), full_page=True)
        await page.get_by_role('button', name='新建问学', exact=True).click()
        assert await page.locator('#question').input_value() == draft
        await open_history(0)
        assert await page.locator('#question').input_value() == '会话一草稿'
        await open_history(1)
        assert await page.locator('.answer-section').count() == 3  # legacy text keeps its words, gains section boundaries
        assert await page.locator('.answer-section p').first.inner_text() == '原文依据不足时，应说明限制。'
        assert await page.locator('.answer-section').first.locator('h3').count() == 0

        async def source_failure(route):
            await route.fulfill(status=503, json={'detail': 'test failure'})

        await page.route('**/api/passages/' + passage['id'], source_failure)
        # Use the known citation passage, independent of the fixture answer's formatting.
        await page.locator('.citations > button').first.click()
        await page.get_by_role('dialog').get_by_role('alert').wait_for()
        assert await page.locator('.source-original').inner_text() == passage['text']
        await page.unroute('**/api/passages/' + passage['id'], source_failure)
        await page.get_by_role('button', name='重试', exact=True).click()
        await page.get_by_role('dialog').get_by_role('alert').wait_for(state='hidden')
        assert await page.get_by_role('button', name='关闭此对话框').count() == 1
        await page.keyboard.press('Escape')

        await page.get_by_role('button', name='典籍文库', exact=True).click()
        await page.locator('.passage-list article').first.wait_for()
        assert await page.locator('nav [aria-current="page"]').inner_text() == '典籍文库'
        assert await page.locator('.passage-list article').count() == 10
        assert await page.locator('.passage-note[open]').count() == 0
        await page.get_by_role('checkbox', name='展开全部释义').check()
        assert await page.locator('.passage-note[open]').count() > 0
        await page.get_by_role('checkbox', name='展开全部释义').uncheck()
        await page.screenshot(path=str(OUT / 'refined-library.png'))
        library_height = await page.evaluate('document.documentElement.scrollHeight')
        await page.get_by_role('button', name='下一页原文', exact=True).click()
        await page.get_by_text('第 11–20 段 · 第 2 / 52 页', exact=True).wait_for()
        await page.locator('.passage-list article').first.wait_for()
        await page.get_by_role('searchbox', name='查找篇章').fill('学而')
        assert await page.locator('.chapter-nav button').count() == 2
        await page.locator('.chapter-nav button').last.click()
        await page.get_by_text('共 16 段原文', exact=True).wait_for()
        assert await page.locator('.chapter-nav [aria-current="true"]').inner_text() == '学而篇'
        await page.get_by_role('searchbox', name='查找篇章').fill('')
        await page.get_by_role('button', name='用这段原文提问').first.click()
        assert '请解释《论语》' in await page.locator('#question').input_value()
        assert not calls
        await page.locator('#question').fill('失败后保留')
        await page.locator('#question').press('Enter')
        await page.get_by_role('alert').wait_for()
        assert await page.locator('#question').input_value() == '失败后保留'
        mode = 'delay'
        await page.locator('#question').fill('停止等待后保留')
        await page.locator('#question').press('Enter')
        await page.get_by_role('button', name='停止等待', exact=True).click()
        await page.get_by_text('已停止等待，问题已保留。', exact=False).wait_for()
        assert await page.locator('#question').input_value() == '停止等待后保留'
        await asyncio.sleep(2.2)
        assert len(calls) == 2

        await page.locator('#question').fill('长' * 1199)
        await page.get_by_role('button', name='典籍文库', exact=True).click()
        await page.locator('.passage-list article').first.wait_for()
        await page.get_by_role('button', name='用这段原文提问').first.click()
        await page.get_by_role('alert').wait_for()
        await page.get_by_role('button', name='问答书房', exact=True).click()
        assert await page.locator('#question').input_value() == '长' * 1199
        assert not errors, errors
        (OUT / 'refinement-checks.json').write_text(json.dumps({
            'desktop_widths': [1100, 1280, 1440, 1920], 'library_height': library_height,
            'model_requests_intercepted': len(calls), 'paid_calls': 0, 'console_errors': errors,
            'checks': ['history metadata/search', 'draft preservation', 'prepare before send', 'legacy and structured answers',
                       'source error/retry/Escape', 'Chinese close names', 'selected semantics', 'notes disclosure',
                       'top pagination', 'chapter finding', 'error recovery', 'stop waiting', 'long draft guard']
        }, ensure_ascii=False, indent=2))
        await browser.close()
        print('Refinement desktop QA passed; no paid calls or stored data changes')


if __name__ == '__main__':
    asyncio.run(main())
