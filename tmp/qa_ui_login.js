/* QA 端到端：真·UI 登录（填账号/密码/图形验证码）+ 点侧边栏菜单进入三个列表，
 * 再抓 el-table 表头与行文本。用来排除"直接改 hash 路由碰巧能渲染"的侥幸情况。
 *
 * 验证码明文在 Redis 对应 db 的 uuid key 里，这里用裸 TCP 走 RESP 读出来回填。
 * 用法: node deploy/tmp/qa_ui_login.js <port> [db]
 */
const { spawn } = require('child_process')
const net = require('net')
const os = require('os')
const path = require('path')

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const DEBUG_PORT = 9334

const port = Number(process.argv[2] || 8081)
const db = Number(process.argv[3] ?? ({ 8081: 0, 8082: 1, 8083: 2, 8084: 3 }[port] ?? 0))

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function redisGet(key, dbIndex) {
  return new Promise((resolve, reject) => {
    const sock = net.createConnection(6379, '127.0.0.1')
    let acc = Buffer.alloc(0)
    let done = false
    const finish = (v) => { if (done) return; done = true; resolve(v); try { sock.end() } catch (e) {} }
    sock.on('error', reject)
    const timer = setTimeout(() => { if (!done) { done = true; try { sock.end() } catch (e) {} reject(new Error('redis 超时 key=' + key)) } }, 6000)
    sock.on('connect', () => {
      const cmd = (arr) => {
        let out = Buffer.from('*' + arr.length + '\r\n')
        arr.forEach((a) => {
          const b = Buffer.from(String(a))
          out = Buffer.concat([out, Buffer.from('$' + b.length + '\r\n'), b, Buffer.from('\r\n')])
        })
        sock.write(out)
      }
      cmd(['SELECT', String(dbIndex)])
      cmd(['GET', key])
    })
    sock.on('data', (d) => {
      acc = Buffer.concat([acc, d])
      const s = acc.toString('binary') // 1 字符 = 1 字节，保证偏移量对齐
      const p1 = s.indexOf('\r\n')
      if (p1 < 0) return
      if (s.slice(0, p1) !== '+OK') { clearTimeout(timer); reject(new Error('SELECT 失败: ' + s.slice(0, p1))); return }
      const rest = s.slice(p1 + 2)
      if (rest.startsWith('$-1')) { clearTimeout(timer); finish(null); return }
      const m = /^\$(\d+)\r\n/.exec(rest)
      if (!m) return
      const n = Number(m[1])
      const start = p1 + 2 + m[0].length
      if (acc.length < start + n + 2) return
      clearTimeout(timer)
      finish(acc.slice(start, start + n).toString('utf8'))
    })
  })
}

const SCRAPE = `(() => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const root = document.querySelector('.el-table');
  if (!root) return JSON.stringify({ ok: false, hash: location.hash });
  const headers = Array.from(root.querySelectorAll('.el-table__header-wrapper th .cell')).map(n => norm(n.innerText));
  const rows = Array.from(root.querySelectorAll('.el-table__body-wrapper tbody tr'))
    .map(tr => Array.from(tr.querySelectorAll('td .cell')).map(n => norm(n.innerText)));
  return JSON.stringify({ ok: true, hash: location.hash, headers, rows });
})()`

const MENUS = ['商户信息', '门店管理', '员工管理']

async function main() {
  const userDataDir = path.join(os.tmpdir(), 'bahar-qa-ui-' + Date.now())
  const chrome = spawn(CHROME, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--no-proxy-server', '--proxy-bypass-list=*',
    '--remote-debugging-port=' + DEBUG_PORT, '--remote-allow-origins=*',
    '--window-size=1600,1000', '--user-data-dir=' + userDataDir, 'about:blank',
  ], { stdio: 'ignore' })

  let version = null
  for (let i = 0; i < 60 && !version; i++) {
    try { const r = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/version`); if (r.ok) version = await r.json() } catch (e) {}
    if (!version) await sleep(500)
  }
  if (!version) throw new Error('DevTools 没起来')

  const list = await (await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/list`)).json()
  const target = list.find((t) => t.type === 'page')
  const ws = new WebSocket(target.webSocketDebuggerUrl)
  const logs = []
  const errors = []
  let id = 0
  const pending = new Map()
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data)
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return }
    if (m.method === 'Runtime.consoleAPICalled') {
      const t = m.params.type
      if (t === 'error' || t === 'warning') logs.push('[' + t + '] ' + (m.params.args || []).map((a) => a.value || a.description || '').join(' '))
    }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails || {}
      errors.push('[exception] ' + ((d.exception && d.exception.description) ? d.exception.description : d.text))
    }
    if (m.method === 'Log.entryAdded') { const e = m.params.entry || {}; if (e.level === 'error') errors.push('[log] ' + e.text + ' url=' + (e.url || '(无)')) }
  }
  const send = (method, params) => new Promise((res) => { const mid = ++id; pending.set(mid, res); ws.send(JSON.stringify({ id: mid, method, params: params || {} })) })
  const ev = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
    return r.result && r.result.result ? r.result.result.value : undefined
  }
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j })
  await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable')

  await send('Page.navigate', { url: `http://127.0.0.1:${port}/admin/index.html#/login` })
  await sleep(4000)

  // 页面自己刷新出来的验证码 uuid 才是登录要用的那个（直接调接口拿到的不是）
  const formUuid = await ev(`(() => {
    const el = document.querySelector('.login-wrap');
    const vm = el && el.__vue__;
    return vm && vm.form ? vm.form.uuid : '';
  })()`)
  if (!formUuid) throw new Error('读不到登录页的 captcha uuid')
  const code = (await redisGet(formUuid, db) || '').replace(/^"|"$/g, '').trim()
  console.log(`端口 ${port}: 页面 captcha uuid=${formUuid} code=${code}`)
  if (!code) throw new Error('Redis 里读不到验证码明文')

  const filled = await ev(`(() => {
    const ins = Array.from(document.querySelectorAll('.login-box input'));
    if (ins.length < 3) return 'input 数量=' + ins.length;
    const set = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); };
    set(ins[0], 'bahar'); set(ins[1], '123456'); set(ins[2], ${JSON.stringify(code)});
    return 'ok:' + ins.map(i => i.value).join('|');
  })()`)
  console.log('  填表:', filled)

  await ev(`(() => { const b = document.querySelector('.login-box button'); if (b) b.click(); return 'clicked'; })()`)
  await sleep(5000)

  const afterLogin = await ev(`JSON.stringify({ hash: location.hash, token: !!localStorage.getItem('bahar-admin-token'), text: (document.body.innerText||'').replace(/\\s+/g,' ').slice(0,120) })`)
  console.log('  登录后:', afterLogin)

  for (const label of MENUS) {
    const clicked = await ev(`(() => {
      const items = Array.from(document.querySelectorAll('.el-menu-item'));
      const hit = items.find(n => (n.innerText||'').replace(/\\s+/g,'').indexOf(${JSON.stringify(label)}) >= 0);
      if (!hit) return 'notfound:' + items.map(n => (n.innerText||'').trim()).join('/');
      const sub = hit.closest('.el-submenu');
      if (sub) { const t = sub.querySelector('.el-submenu__title'); if (t) t.click(); }
      return 'clicked:' + hit.getAttribute('index');
    })()`)
    await sleep(900)
    let snap = null
    for (let i = 0; i < 25; i++) {
      const clicked2 = await ev(`(() => {
        const items = Array.from(document.querySelectorAll('.el-menu-item'));
        const hit = items.find(n => (n.innerText||'').replace(/\\s+/g,'').indexOf(${JSON.stringify(label)}) >= 0);
        if (hit && !hit.className.includes('is-active')) { hit.click(); return 1; }
        return 0;
      })()`)
      await sleep(900)
      const v = await ev(SCRAPE)
      if (v) { const o = JSON.parse(v); if (o.ok && o.rows && o.rows.length) { snap = o; break } }
    }
    if (!snap) { console.log(`  [${label}] !! 未渲染  (${clicked})`); continue }
    console.log(`  [${label}] hash=${snap.hash}`)
    console.log(`     表头: ${JSON.stringify(snap.headers)}`)
    console.log(`     行1 : ${JSON.stringify(snap.rows[0])}`)
  }

  console.log('  console 报错/警告: ' + (logs.length ? JSON.stringify(logs.slice(0, 8)) : '(无)'))
  console.log('  未捕获异常: ' + (errors.length ? JSON.stringify(errors.slice(0, 5)) : '(无)'))
  ws.close(); chrome.kill()
}

main().catch((e) => { console.error('FAILED:', e.stack || e.message); process.exit(1) })
