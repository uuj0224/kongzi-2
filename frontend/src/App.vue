<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import Icon from './Icon.vue'
import QuestionComposer from './QuestionComposer.vue'

type Passage = { id: string; book: string; chapter: string; section: number; text: string; note?: string; source_url: string; kind: string }
type Message = { id: number; question: string; answer: string; citations: Passage[]; candidates: Passage[]; elapsed_ms: number; status: string }
type Book = { name: string; kind: string; count: number; chapters: string[] }
const view = ref('chat'), busy = ref(false), error = ref(''), notice = ref('')
const cid = ref<string>(), messages = ref<Message[]>([]), pendingQuestion = ref('')
const drafts = ref<Record<string, string>>({})
const question = computed({
  get: () => drafts.value[cid.value ?? 'new'] ?? '',
  set: (value: string) => { drafts.value[cid.value ?? 'new'] = value },
})
type History = { id: string; title: string; full_title?: string; updated_at: string; message_count: number; preview: string }
const histories = ref<History[]>([]), historyQuery = ref(''), books = ref<Book[]>([])
const historyRefreshing = ref(false), historyError = ref('')
const activeBook = ref('论语'), chapter = ref(''), query = ref(''), page = ref(1), total = ref(0)
const passages = ref<Passage[]>([]), selected = ref<Passage>()
const status = ref({ model_configured: false, index_ready: false, passages: 0 })
const ready = ref(false), initialBusy = ref(true), historyBusy = ref(false), browseBusy = ref(false)
const turns = ref<HTMLElement>(), copiedId = ref<number>(), copyingId = ref<number>()
const historyOpen = ref(false)
const pageSize = 10
const chapterQuery = ref(''), expandedNotes = ref(false)
const sourceBusy = ref(false), sourceError = ref('')
let chatController: AbortController | undefined
const isLanding = computed(() => view.value === 'chat' && !messages.value.length && !busy.value && !historyBusy.value)
function prepareQuestion(text: string) {
  if (busy.value || historyBusy.value) return
  const draft = question.value.trim()
  const prepared = draft && draft !== text ? draft + '\n\n' + text : text
  if (prepared.length > 1200) { error.value = '当前草稿较长，无法再加入这段内容。请先发送或缩短草稿，已有文字已保留。'; return }
  question.value = prepared; error.value = ''; notice.value = '问题已准备好，可以补充或修改后再发送。'; view.value = 'chat'
  nextTick(() => document.getElementById('question')?.focus())
}
function preparePassage(p: Passage) {
  prepareQuestion('请解释《' + p.book + '》' + p.chapter + '中的这段话：' + p.text.slice(0, 850))
}
let browseVersion = 0
let copyVersion = 0
const examples = ['学习与思考应该如何结合？', '孔子出生在哪里？字是什么？', '如何理解“己所不欲，勿施于人”？', '《礼记》如何看待教学相长？']
const chapters = computed(() => books.value.find(b => b.name === activeBook.value)?.chapters || [])
const filteredChapters = computed(() => chapters.value.filter(c => c.includes(chapterQuery.value.trim())))
const filteredHistories = computed(() => histories.value.filter(h => [h.full_title || h.title, h.preview].join(' ').includes(historyQuery.value.trim())))
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const resultRange = computed(() => total.value ? `${(page.value - 1) * pageSize + 1}–${Math.min(page.value * pageSize, total.value)}` : '0')
function historyDate(value: string) {
  if (!value) return ''
  const date = new Date(value.includes('T') ? value : value.replace(' ', 'T') + 'Z')
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
const connected = computed(() => ready.value && status.value.model_configured && status.value.index_ready)

async function api(path: string, init?: RequestInit) {
  let response: Response
  try { response = await fetch('/api' + path, init) }
  catch (e) { if (e instanceof DOMException && e.name === 'AbortError') throw e; throw new Error('暂时无法连接服务。请检查网络连接后重试。') }
  let data
  try { data = await response.json() }
  catch (e) { if (e instanceof DOMException && e.name === 'AbortError') throw e; throw new Error('服务暂时无法响应。请稍后重试。') }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '输入内容不符合要求，请检查后重试。')
  return data
}
async function refreshHistory() { histories.value = await api('/conversations') }
function report(e: unknown) { error.value = e instanceof Error ? e.message : '请求失败，请稍后重试。' }
async function scrollEnd() {
  await nextTick()
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  turns.value?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'end' })
}
async function send() {
  if (busy.value || historyBusy.value) return
  const input = question.value.trim()
  if (!input) return
  question.value = input; pendingQuestion.value = input; busy.value = true; error.value = ''; notice.value = ''; view.value = 'chat'
  chatController = new AbortController()
  await scrollEnd()
  try {
    const data = await api('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: input, conversation_id: cid.value }), signal: chatController.signal })
    question.value = ''; cid.value = data.conversation_id; messages.value.push(data)
    await refreshHistory()
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') notice.value = '已停止等待，问题已保留。后台可能仍在生成，完成后可在问学记录中查看。'
    else report(e)
  }
  finally { busy.value = false; pendingQuestion.value = ''; chatController = undefined; await scrollEnd() }
}
function stopWaiting() { chatController?.abort() }
function newChat() {
  if (busy.value || historyBusy.value) return
  cid.value = undefined; messages.value = []; error.value = ''; notice.value = ''; view.value = 'chat'; copiedId.value = undefined
  nextTick(() => document.getElementById('question')?.focus())
}
async function openChat(id: string) {
  if (busy.value || historyBusy.value) return
  historyOpen.value = false; historyBusy.value = true; error.value = ''; view.value = 'chat'
  try {
    const data = await api('/conversations/' + id)
    cid.value = id; messages.value = data.messages; notice.value = ''; copiedId.value = undefined
  } catch (e) { report(e) }
  finally { historyBusy.value = false; await scrollEnd() }
}
async function browse(reset = false) {
  if (reset) page.value = 1
  const version = ++browseVersion
  browseBusy.value = true; error.value = ''
  try {
    const params = new URLSearchParams({ book: activeBook.value, chapter: chapter.value, q: query.value, page: String(page.value), page_size: String(pageSize) })
    const data = await api('/passages?' + params)
    if (version === browseVersion) { passages.value = data.items; total.value = data.total }
  } catch (e) { if (version === browseVersion) report(e) }
  finally { if (version === browseVersion) browseBusy.value = false }
}
async function showLibrary() { error.value = ''; view.value = 'library'; await browse() }
async function changePage(next: number) {
  if (browseBusy.value || next < 1 || next > pageCount.value) return
  page.value = next; await browse(); await nextTick()
  document.getElementById('library-results')?.scrollIntoView({ block: 'start' })
}
async function openHistory() {
  historyOpen.value = true; historyRefreshing.value = true; historyError.value = ''
  try { await refreshHistory() }
  catch { historyError.value = '暂时无法更新问学记录，请重试。' }
  finally { historyRefreshing.value = false }
}
async function showSource(p: Passage) {
  selected.value = p; sourceBusy.value = true; sourceError.value = ''
  try {
    const data = await api('/passages/' + encodeURIComponent(p.id))
    if (selected.value?.id === p.id) selected.value = data
  } catch { if (selected.value?.id === p.id) sourceError.value = '暂时无法核对最新出处。下方保留已有原文，请重试。' }
  finally { if (selected.value?.id === p.id) sourceBusy.value = false }
}
function answerBlocks(answer: string) {
  return answer.replace(/\r\n?/g, '\n')
    .replace(/([。！？；])(?=(?:核心理解|原文依据|现代延伸解读|资料边界|需要注意)[：:，])/g, '$1\n')
    .split(/\n+/).filter(text => text.trim()).map(text => {
      const title = text.match(/^(?:#{1,3}\s*)?(核心理解|原文依据|现代延伸解读|资料边界|需要注意)(?:[：:，]\s*|\s*$)/)
      return { title: title?.[1], text: title ? text.slice(title[0].length) : text }
    })
}
function answerParts(text: string, m: Message) {
  return text.split(/(\[[^\[\]\n]+\])/g).map(text => ({ text, citation: text.startsWith('[') ? m.citations.find(p => p.id === text.slice(1, -1)) : undefined }))
}
async function copyAnswer(m: Message) {
  const version = ++copyVersion
  copyingId.value = m.id
  try {
    await navigator.clipboard.writeText(m.answer)
    copiedId.value = m.id
    window.setTimeout(() => { if (copyVersion === version) copiedId.value = undefined }, 2500)
  } catch { error.value = '浏览器未允许复制，请选中回答文字后复制。' }
  finally { copyingId.value = undefined }
}
onMounted(async () => {
  try {
    const [health, catalog] = await Promise.all([api('/health'), api('/catalog')])
    status.value = health; books.value = catalog; await refreshHistory(); ready.value = true
  } catch (e) { report(e) }
  finally { initialBusy.value = false }
})
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <a class="brand" href="#" @click.prevent="newChat"><span class="seal">孔</span><span>孔子问答<small>与经典对话</small></span></a>
      <nav aria-label="主导航"><button :class="{active: view === 'chat'}" :aria-current="view === 'chat' ? 'page' : undefined" @click="view = 'chat'">问答书房</button><button :class="{active: view === 'library'}" :aria-current="view === 'library' ? 'page' : undefined" @click="showLibrary">典籍文库</button></nav>
      <div class="header-actions"><span class="connection" :class="{online: connected}" role="status" aria-live="polite"><i></i>{{ initialBusy ? '正在连接' : connected ? '知识库已就绪' : '服务待就绪' }}</span><button class="history-trigger" @click="openHistory"><Icon name="clock" :size="17" />问学记录<span>{{ histories.length }}</span></button><button v-if="!isLanding" class="new-chat" :disabled="busy || historyBusy" @click="newChat"><Icon name="plus" :size="16" />新建问学</button></div>
    </header>
    <main>
      <div v-if="ready && (!status.model_configured || !status.index_ready)" class="notice setup" role="status">服务尚未就绪，请检查后端配置。典籍文库可直接阅读。</div>
      <section v-if="isLanding" class="landing" aria-label="问答书房首页">
        <div class="exhibition-hero">
          <img class="hero-art" src="/images/confucius-study.webp" width="1920" height="960" alt="孔子在书院展读竹简，远山与庭院相映的 AI 水墨设色画卷" fetchpriority="high">
          <div class="hero-copy"><h1>有所问，<br><span>亦有所得。</span></h1><p class="intro">从一句古文，到一个生活中的困惑。<br>循着先贤的足迹，让经典回应当下。</p>
<QuestionComposer v-model="question" :busy="busy" :locked="historyBusy" :error="error" :notice="notice" @stop="stopWaiting" @clear-error="error = ''" @submit="send()" />
          </div>
        </div>
        <div class="art-caption"><span>孔子读书图 · AI 艺术创作</span><span>以文会友，以问求知。</span></div>
        <section class="discovery"><div class="discovery-heading"><h2>从一个问题，走近孔子。</h2><p>学习、交友、修身，与千年前的思想相遇。</p></div><div class="suggestions"><button v-for="q in examples" :key="q" @click="prepareQuestion(q)"><span>{{ q }}</span><Icon name="arrow" :size="18" /></button></div></section>
        <div class="collection-link"><p><span>典籍为据</span>《论语》<b>·</b>《史记》<b>·</b>《礼记》</p><button class="text-button" @click="showLibrary">展卷阅读<Icon name="arrow" :size="17" /></button></div>
      </section>
      <section v-else-if="view === 'chat'" class="chat-page has-messages"><div class="conversation-title"><span>问答书房</span><span>AI 模拟解读 · 有据可循</span></div>
        <div v-if="historyBusy" class="answer-skeleton" role="status" aria-label="正在读取会话"><span></span><span></span><span></span></div>
        <div v-else-if="messages.length || busy" class="thread" aria-live="polite">
          <article v-for="m in messages" :key="m.id" class="turn">
            <div class="question"><span class="question-mark">问</span><h2>{{ m.question }}</h2></div>
            <div class="answer-label"><span class="scholar-avatar" aria-hidden="true"><img src="/images/confucius-portrait.webp" width="640" height="800" alt=""></span><span class="guide-identity">经典解读<small>孔子形象 · AI 模拟</small></span><span class="answer-state" :class="{ warning: m.status !== 'ok' }">{{ m.status === 'insufficient' ? '资料不足' : m.status === 'citation_warning' ? '引用待核验' : '依据文献整理' }}</span></div>
            <div class="answer"><section v-for="(block, b) in answerBlocks(m.answer)" :key="b" class="answer-section"><h3 v-if="block.title">{{ block.title }}</h3><p v-if="block.text"><template v-for="(part, i) in answerParts(block.text, m)" :key="i"><button v-if="part.citation" class="inline-citation" :aria-label="'查看引用 ' + (m.citations.findIndex(p => p.id === part.citation?.id) + 1) + '：《' + part.citation.book + '》' + part.citation.chapter + '第' + part.citation.section + '段原文'" :title="'查看《' + part.citation.book + '》' + part.citation.chapter + '原文'" @click="showSource(part.citation)">{{ m.citations.findIndex(p => p.id === part.citation?.id) + 1 }}</button><template v-else>{{ part.text }}</template></template></p></section></div>
            <div v-if="m.citations.length" class="citations"><p class="source-heading"><Icon name="book" :size="16" />本次回答引用<span>{{ m.citations.length }} 条原文</span></p><button v-for="p in m.citations" :key="p.id" @click="showSource(p)"><span class="citation-title">{{ p.book }} · {{ p.chapter }} {{ p.section }}<small>{{ p.text.slice(0, 65) }}{{ p.text.length > 65 ? '…' : '' }}</small></span><span class="citation-kind">{{ p.kind }}<Icon name="external" :size="14" /></span></button></div>
            <details v-if="m.candidates?.length" class="candidates"><summary>查看检索候选原文<span>候选不代表已支持答案</span></summary><button v-for="p in m.candidates" :key="p.id" class="candidate" @click="showSource(p)"><span>{{ p.book }} · {{ p.chapter }} {{ p.section }}</span>{{ p.text.slice(0, 65) }}…</button></details>
            <div class="answer-tools"><span><Icon name="clock" :size="14" />{{ (m.elapsed_ms / 1000).toFixed(1) }} 秒</span><button class="text-button" :disabled="copyingId === m.id" @click="copyAnswer(m)"><Icon :name="copiedId === m.id ? 'check' : 'copy'" :size="15" /><span aria-live="polite">{{ copiedId === m.id ? '已复制' : '复制回答' }}</span></button></div>
          </article>
          <div v-if="busy" class="pending-turn"><div class="question"><span class="question-mark">问</span><h2>{{ pendingQuestion }}</h2></div><div class="thinking" role="status"><span class="thinking-dot"></span>正在查阅典籍、整理回答，请稍候…</div><div class="answer-skeleton" aria-hidden="true"><span></span><span></span><span></span></div></div>
          <div ref="turns"></div>
        </div>
<QuestionComposer v-model="question" :busy="busy" :locked="historyBusy" :error="error" :notice="notice" @stop="stopWaiting" @clear-error="error = ''" @submit="send()" />
      </section>
      <section v-if="view === 'library'" class="library">
        <div v-if="error" class="notice error" role="alert"><span>{{ error }}</span><button @click="error = ''" aria-label="关闭错误提示"><Icon name="close" /></button></div>
        <div class="library-heading"><div><h1>展卷，有所见。</h1><p>保留文献出处，在不同记述之间认识孔子。</p></div><span class="library-summary">{{ books.length }} 部典籍<span>原典 · 史传 · 后世记述</span></span></div>
        <div class="book-tabs" role="group" aria-label="选择典籍"><button v-for="b in books" :key="b.name" :class="{ selected: b.name === activeBook }" :aria-pressed="b.name === activeBook" @click="activeBook = b.name; chapter = ''; chapterQuery = ''; browse(true)"><Icon name="book" :size="19" /><span>{{ b.name }}<small>{{ b.kind }}</small></span><span class="book-count">{{ b.count }} 段</span></button></div>
        <div class="reader-layout"><aside class="chapter-nav" aria-label="章节目录"><h2>篇章目录</h2><label class="chapter-search"><span class="sr-only">查找篇章</span><input v-model="chapterQuery" type="search" placeholder="查找篇章"></label><button :class="{ selected: !chapter }" :aria-current="!chapter ? 'true' : undefined" @click="chapter = ''; browse(true)">全部篇章</button><button v-for="c in filteredChapters" :key="c" :class="{ selected: chapter === c }" :aria-current="chapter === c ? 'true' : undefined" @click="chapter = c; browse(true)">{{ c }}</button><p v-if="!filteredChapters.length" class="chapter-empty" role="status">没有匹配篇章，试试更短的词。</p></aside><div class="reader-body">
        <form class="filters" @submit.prevent="browse(true)"><label for="chapter">篇章</label><select id="chapter" v-model="chapter" @change="browse(true)"><option value="">全部篇章</option><option v-for="c in chapters" :key="c">{{ c }}</option></select><label class="search-field" for="search"><Icon name="search" :size="17" /><span class="sr-only">搜索原文或整理释义</span><input id="search" v-model="query" placeholder="搜索原文或整理释义"></label><el-button native-type="submit" :loading="browseBusy">查找</el-button><button v-if="query || chapter" type="button" class="text-button clear-filters" @click="query = ''; chapter = ''; browse(true)">重置</button></form>
        <div id="library-results" class="list-heading"><span>{{ activeBook }}<span v-if="chapter"> · {{ chapter }}</span></span><span role="status">{{ browseBusy ? '正在查阅…' : '共 ' + total + ' 段原文' }}</span></div>
        <div class="reader-toolbar"><span>第 {{ resultRange }} 段 · 第 {{ page }} / {{ pageCount }} 页</span><label class="note-toggle"><input v-model="expandedNotes" type="checkbox">展开全部释义</label><div class="page-actions"><el-button :disabled="page <= 1 || browseBusy" aria-label="上一页原文" @click="changePage(page - 1)">上一页</el-button><el-button :disabled="page >= pageCount || browseBusy" aria-label="下一页原文" @click="changePage(page + 1)">下一页</el-button></div></div>
        <div class="passage-list" :aria-busy="browseBusy">
          <template v-if="browseBusy"><div v-for="i in 3" :key="i" class="answer-skeleton" aria-hidden="true"><span></span><span></span><span></span></div></template>
          <template v-else><article v-for="p in passages" :key="p.id"><div class="passage-meta"><span>{{ p.chapter }} · {{ p.section }}</span><button class="text-button" @click="showSource(p)">查看出处<Icon name="external" :size="14" /></button></div><p class="original">{{ p.text }}</p><details v-if="p.note" :key="p.id + String(expandedNotes)" class="note passage-note" :open="expandedNotes"><summary>项目整理释义<span>非权威译注</span></summary><p>{{ p.note }}</p></details><button class="ask-passage text-button" @click="preparePassage(p)" :disabled="busy || historyBusy">用这段原文提问<Icon name="arrow" :size="16" /></button></article><div v-if="!passages.length" class="empty-results"><Icon name="search" :size="28" /><h2>没有找到相关原文</h2><p>试试更短的词语，或清除篇章和搜索条件后重新查找。</p><el-button @click="query = ''; chapter = ''; browse(true)">清除筛选</el-button></div></template>
        </div>
        <div class="pagination"><el-button :disabled="page <= 1 || browseBusy" @click="changePage(page - 1)">上一页</el-button><span>第 {{ page }} / {{ pageCount }} 页</span><el-button :disabled="page >= pageCount || browseBusy" @click="changePage(page + 1)">下一页</el-button></div>
        </div></div>
      </section>

      <footer class="footer"><span>孔子问答</span><span>读经典，也读生活。</span><span>{{ status.passages }} 段文献 · 原文可追溯</span></footer>
    </main>
    <el-drawer v-model="historyOpen" title="问学记录" size="360px">
      <p class="drawer-intro">重读已有问答。每次提问独立回答，追问时请写明背景。</p>
      <p v-if="historyRefreshing" class="source-loading" role="status">正在更新记录…</p>
      <div v-if="historyError" class="notice error" role="alert"><span>{{ historyError }}</span><button class="text-button" @click="openHistory">重试</button></div>
      <label class="search-field history-search"><Icon name="search" :size="17" /><span class="sr-only">搜索问学记录</span><input v-model="historyQuery" type="search" placeholder="搜索问题或摘要"></label>
      <div class="histories"><p v-if="initialBusy">正在读取记录…</p><p v-else-if="!histories.length">还没有问学记录，从一个问题开始。</p><div v-else-if="!filteredHistories.length" class="history-empty" role="status"><p>没有匹配的问学记录。</p><button class="text-button" @click="historyQuery = ''">清除搜索</button></div>
        <button v-for="h in filteredHistories" :key="h.id" :class="{chosen: cid === h.id}" :aria-current="cid === h.id ? 'true' : undefined" :title="h.full_title || h.title" :disabled="busy || historyBusy" @click="openChat(h.id)"><span class="history-entry"><strong>{{ h.full_title || h.title }}</strong><small>{{ historyDate(h.updated_at) }} · {{ h.message_count }} 次问答</small><span v-if="h.preview" class="history-preview">{{ h.preview }}</span></span><Icon name="chevron" :size="15" /></button>
      </div>
    </el-drawer>
    <el-dialog :model-value="!!selected" title="原文与出处" width="680px" @close="selected = undefined"><template v-if="selected">
      <p v-if="sourceBusy" role="status" class="source-loading">正在核对出处…</p><div v-if="sourceError" class="notice error" role="alert"><span>{{ sourceError }}</span><button class="text-button" @click="showSource(selected)">重试</button></div>
      <div class="source-meta"><span>{{ selected.kind }}</span><span>{{ selected.id }}</span></div><h2>{{ selected.book }} · {{ selected.chapter }} {{ selected.section }}</h2><p class="original source-original">{{ selected.text }}</p><div v-if="selected.note" class="note"><b>项目整理释义 · 非权威译注</b><p>{{ selected.note }}</p></div><p class="source-disclaimer">章句编号依当前资料底本；长篇按项目分段编号。史传和后世记述不直接等同于孔子原话。</p><a class="source-link" :href="selected.source_url" target="_blank" rel="noopener noreferrer">查看原始资料<Icon name="external" :size="15" /></a><p class="source-version">资料保存于 GitHub 固定版本，便于核对出处。</p>
    </template></el-dialog>
  </div>
</template>
