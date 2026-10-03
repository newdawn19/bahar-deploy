/* 真实浏览器验证某个菜单页能不能渲染出数据。
 *
 * 为什么不用 curl：前端的请求方法自适应、模板编译、表格渲染全是浏览器侧行为，
 * curl 只能验证后端接口，验证不了"页面有没有数据"。
 * 这里注入 token 绕过验证码，直接看表格行数和控制台报错。
 *
 * 用法: NODE_PATH=<workspace>/node_modules node deploy/tools/verify-page.js <port> <路由>
 *  例: node deploy/tools/verify-page.js 8083 /goods
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = process.argv[2] || '8083';
const ROUTE = process.argv[3] || '/goods';
const LOG_MAP = {
  '8081': 'D:/logs/bahar/server.log',
  '8082': 'D:/logs/bahar-car/server.log',
  '8083': 'D:/logs/bahar-food/server.log',
  '8084': 'D:/logs/bahar-health/server.log'
};
const BASE = 'http://127.0.0.1:' + PORT;

async function api(p, payload, method, token) {
  const headers = { 'platform': 'PC', 'Content-Type': 'application/json' };
  if (token) { headers['Access-Token'] = token; }
  const res = await fetch(BASE + p, {
    method: method || 'GET',
    headers,
    body: payload ? JSON.stringify(payload) : undefined
  });
  return res.json();
}

async function login() {
  const cap = await api('/clientApi/captcha/getCode');
  const uuid = (cap.data || {}).uuid;
  const logFile = LOG_MAP[PORT];
  let code = null;
  if (fs.existsSync(logFile)) {
    const txt = fs.readFileSync(logFile, 'utf8');
    const re = /生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)/g;
    let m;
    while ((m = re.exec(txt)) !== null) {
      if (m[2].trim() === String(uuid).trim()) { code = m[1].trim(); }
    }
  }
  if (!code) { throw new Error('没读到验证码，日志: ' + logFile); }
  const r = await api('/backendApi/login/doLogin',
    { username: 'bahar', password: '123456', captchaCode: code, uuid: uuid }, 'POST');
  return (r.data || {}).token;
}

(async () => {
  const token = await login();
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--no-proxy-server']
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') { errors.push('console: ' + m.text()); } });
  page.on('requestfailed', r => errors.push('reqfail: ' + r.url()));

  // 先落地到登录页，把 token 与方法缓存写好（方法缓存清空 = 模拟首次访问）
  await page.goto(BASE + '/admin/index.html', { waitUntil: 'networkidle2' });
  await page.evaluate((t) => {
    localStorage.setItem('bahar-admin-token', t);
    localStorage.removeItem('bahar-admin-methods');
  }, token);

  await page.goto(BASE + '/admin/index.html#' + ROUTE, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 3500));

  const info = await page.evaluate(() => {
    const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
    const empty = document.querySelector('.el-table__empty-text');
    return {
      title: document.querySelector('.el-menu-item.is-active') ?
        document.querySelector('.el-menu-item.is-active').innerText.trim() : '',
      rowCount: rows.length,
      emptyText: empty ? empty.innerText.trim() : '',
      firstRow: rows.length ? rows[0].innerText.replace(/\s+/g, ' ').slice(0, 120) : '',
      methods: localStorage.getItem('bahar-admin-methods') || '(空)'
    };
  });

  console.log('===== ' + PORT + ' ' + ROUTE + ' =====');
  console.log('菜单       : ' + info.title);
  console.log('表格行数   : ' + info.rowCount);
  console.log('空态提示   : ' + (info.emptyText || '(无)'));
  console.log('首行       : ' + (info.firstRow || '(无)'));
  console.log('方法缓存   : ' + info.methods);
  console.log('报错       : ' + (errors.length ? '\n  - ' + errors.join('\n  - ') : '无'));
  await browser.close();
  process.exit(info.rowCount > 0 && errors.length === 0 ? 0 : 1);
})().catch(e => { console.error('失败: ' + e.message); process.exit(2); });
