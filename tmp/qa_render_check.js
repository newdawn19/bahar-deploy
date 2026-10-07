/* QA 渲染层验证：用真实 Chrome（CDP）打开四套后台的商户/门店/员工三个列表，
 * 抓 el-table 的真实表头文本与行数据文本，验证「门店数/员工数/所属商户/所属门店/关联会员」
 * 是否真的渲染出来（重点：员工列表的 type:'expr' 自定义列）。
 *
 * 为什么不用 puppeteer：本机没装。Node 22 自带 WebSocket / fetch，直接走 CDP 就够。
 * 为什么必须 --no-proxy-server：本机 http_proxy=127.0.0.1:50078 会把 127.0.0.1 也代理掉并 502。
 *
 * 用法: node deploy/tmp/qa_render_check.js [port...]
 */
const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')
const os = require('os')

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const DEBUG_PORT = 9333
const TOKENS = JSON.parse(fs.readFileSync(path.join(__dirname, 'qa_tokens.json'), 'utf-8'))
const ROUTES = ['merchant', 'store', 'staff']

const args = process.argv.slice(2)
const PORTS = args.length ? args.map(Number) : Object.keys(TOKENS).map(Number)

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

let chromeProc = null

function startChrome() {
  const userDataDir = path.join(os.tmpdir(), 'bahar-qa-chrome-' + Date.now())
  chromeProc = spawn(CHROME, [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--no-proxy-server',
    '--proxy-bypass-list=*',
    '--remote-debugging-port=' + DEBUG_PORT,
    '--remote-allow-origins=*',
    '--window-size=1600,1000',
    '--user-data-dir=' + userDataDir,
    'about:blank',
  ], { stdio: 'ignore' })
}

async function waitForDevTools() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/version`)
      if (r.ok) return await r.json()
    } catch (e) { /* 还没起来 */ }
    await sleep(500)
  }
  throw new Error('Chrome DevTools 端口没起来')
}

class Session {
  constructor(ws) {
    this.ws = ws
    this.id = 0
    this.pending = new Map()
    this.logs = []
    this.errors = []
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.id && this.pending.has(msg.id)) {
        this.pending.get(msg.id)(msg)
        this.pending.delete(msg.id)
        return
      }
      if (msg.method === 'Runtime.consoleAPICalled') {
        const t = msg.params.type
        if (t === 'error' || t === 'warning') {
          this.logs.push('[' + t + '] ' + (msg.params.args || [])
            .map((a) => a.value || a.description || '').join(' '))
        }
      }
      if (msg.method === 'Runtime.exceptionThrown') {
        const d = msg.params.exceptionDetails || {}
        this.errors.push('[exception] ' +
          ((d.exception && d.exception.description) ? d.exception.description : d.text))
      }
      if (msg.method === 'Log.entryAdded') {
        const e = msg.params.entry || {}
        if (e.level === 'error') this.errors.push('[log] ' + (e.text || ''))
      }
    }
  }

  send(method, params) {
    const mid = ++this.id
    return new Promise((res, rej) => {
      this.pending.set(mid, res)
      this.ws.send(JSON.stringify({ id: mid, method, params: params || {} }))
      setTimeout(() => { if (this.pending.has(mid)) { this.pending.delete(mid); rej(new Error('CDP 超时: ' + method)) } }, 30000)
    })
  }

  async evalJs(expression) {
    const r = await this.send('Runtime.evaluate', {
      expression, returnByValue: true, awaitPromise: true,
    })
    if (r.result && r.result.exceptionDetails) {
      throw new Error('evaluate 异常: ' + JSON.stringify(r.result.exceptionDetails).slice(0, 300))
    }
    return r.result && r.result.result ? r.result.result.value : undefined
  }
}

const SCRAPE = `(() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  // el-table 有 fixed 列时会复制出多份 table，去重按 header-wrapper 所属的根 .el-table
  const roots = Array.from(document.querySelectorAll('.el-table'));
  const tables = roots.map((root) => {
    const headers = Array.from(root.querySelectorAll('.el-table__header-wrapper th .cell'))
      .map((n) => norm(n.innerText));
    const bodyRows = Array.from(root.querySelectorAll('.el-table__body-wrapper tbody tr'))
      .map((tr) => Array.from(tr.querySelectorAll('td .cell')).map((n) => norm(n.innerText)));
    return { headers, rows: bodyRows };
  }).filter((t) => t.headers.length);
  return JSON.stringify({
    url: location.href,
    title: document.title,
    tables,
    bodyText: norm(document.body.innerText).slice(0, 400)
  });
})()`

async function main() {
  startChrome()
  const version = await waitForDevTools()
  console.log('Chrome:', version['Browser'])

  const list = await (await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/list`)).json()
  let target = list.find((t) => t.type === 'page')
  if (!target) {
    target = await (await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/new?about:blank`, { method: 'PUT' })).json()
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j })
  const s = new Session(ws)
  await s.send('Runtime.enable')
  await s.send('Log.enable')
  await s.send('Page.enable')

  const results = {}

  for (const port of PORTS) {
    const tk = TOKENS[String(port)]
    if (!tk) { console.log(`\n!! 端口 ${port} 没有 token，跳过`); continue }
    results[port] = { name: tk.name, routes: {} }
    console.log(`\n############ ${tk.name}  端口 ${port} ############`)

    // 1) 先落到登录页（同源），注入 token
    await s.send('Page.navigate', { url: `http://127.0.0.1:${port}/admin/index.html#/login` })
    await sleep(3500)
    const injected = await s.evalJs(
      `(() => { localStorage.setItem('bahar-admin-token', ${JSON.stringify(tk.token)});
                return localStorage.getItem('bahar-admin-token') ? 'ok' : 'fail'; })()`)
    console.log('  注入 token:', injected)

    for (const route of ROUTES) {
      s.logs.length = 0
      s.errors.length = 0
      await s.send('Page.navigate', { url: `http://127.0.0.1:${port}/admin/index.html#/${route}` })
      // 轮询等表格出现
      let snap = null
      for (let i = 0; i < 30; i++) {
        await sleep(800)
        try {
          const v = await s.evalJs(SCRAPE)
          if (v) {
            const o = JSON.parse(v)
            if (o.tables && o.tables.length) { snap = o; break }
          }
        } catch (e) { /* 页面还没稳 */ }
        snap = null
      }
      if (!snap) {
        console.log(`  ---- /#/${route} ----  !! 30s 内没抓到 el-table`)
        results[port].routes[route] = { error: 'no table' }
        continue
      }
      const t = snap.tables[0]
      console.log(`  ---- /#/${route} ----`)
      console.log('  表头: ' + JSON.stringify(t.headers, null, 0))
      t.rows.slice(0, 4).forEach((row, i) => {
        console.log(`  行${i + 1}: ` + JSON.stringify(row, null, 0))
      })
      console.log(`  (共 ${t.rows.length} 行)`)
      if (s.logs.length) console.log('  console: ' + JSON.stringify(s.logs.slice(0, 6)))
      if (s.errors.length) console.log('  !! 异常: ' + JSON.stringify(s.errors.slice(0, 4)))
      results[port].routes[route] = {
        headers: t.headers,
        rows: t.rows,
        logs: s.logs.slice(0, 10),
        errors: s.errors.slice(0, 6),
      }
    }
  }

  fs.writeFileSync(path.join(__dirname, 'qa_render_result.json'),
    JSON.stringify(results, null, 2), 'utf-8')
  console.log('\n结果已写入 deploy/tmp/qa_render_result.json')

  ws.close()
  if (chromeProc) chromeProc.kill()
}

main().catch((e) => {
  console.error('FAILED:', e.stack || e.message)
  if (chromeProc) chromeProc.kill()
  process.exit(1)
})
