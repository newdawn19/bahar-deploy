/* 后台全菜单渲染体检（单浏览器会话版）

   为什么这样写：
   1. 每个菜单起一次 Chrome = 76 次冷启动，十几分钟还容易超时；这里复用
      一个页面实例，靠改 location.hash 切路由，只等网络空闲，快一个数量级。
   2. 「接口通」不等于「页面有数据」——最近一次线上问题就是 goods/list 返回
      200 带 3 条数据，表格却全白。所以这里必须看真实 DOM 的行数。

   用法:
     export NODE_PATH=C:/Users/Lenovo/.workbuddy/binaries/node/workspace/node_modules
     export MSYS_NO_PATHCONV=1
     node deploy/tools/sweep-admin.js [port...]
*/
const fs = require('fs');
// puppeteer-core 装在 workbuddy 的隔离 workspace 里，不在项目 node_modules。
// 正常跑法要 export NODE_PATH=...，忘了就报 MODULE_NOT_FOUND，所以这里兜底补一次。
let puppeteer;
try {
  puppeteer = require('puppeteer-core');
} catch (e) {
  const fallback = 'C:/Users/Lenovo/.workbuddy/binaries/node/workspace/node_modules';
  if (fs.existsSync(fallback)) module.paths.push(fallback);
  puppeteer = require('puppeteer-core');
}

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
// 通用 19 菜单 + 按端口追加的行业/增值菜单（与 modules.js 的 PORT_EXTRAS 保持一致）：
//   汽车 8082 独有 vehicle/vehicleOrder；餐饮 8083 独有 table/tableArea；
//   退款/分销/预约/报表 汽车餐饮康养有、零售没有。零售 8081 只有通用菜单。
const BASE_MENUS = [
  ['member', '会员管理'], ['grade', '会员等级'], ['group', '会员分组'],
  ['tag', '会员标签'], ['cate', '商品分类'], ['goods', '商品服务'],
  ['stock', '库存管理'], ['coupon', '卡券管理'], ['userCoupon', '卡券核销'],
  ['order', '订单管理'], ['store', '门店管理'], ['staff', '员工管理'],
  ['printer', '打印设备'], ['merchant', '商户信息'], ['article', '文章公告'],
  ['banner', '首页轮播'], ['account', '后台账号'], ['duty', '角色职务'],
  ['actlog', '操作日志']
];
const VALUE_MENUS = [
  ['refund', '退款管理'], ['commissionLog', '分销佣金'],
  ['book', '预约项目'], ['report', '经营报表']
];
const PORT_MENUS = {
  '8081': BASE_MENUS,
  '8082': BASE_MENUS.concat(
    [['vehicle', '车辆档案'], ['vehicleOrder', '车辆服务单']], VALUE_MENUS),
  '8083': BASE_MENUS.concat(
    [['table', '桌台管理'], ['tableArea', '桌台区域']], VALUE_MENUS),
  '8084': BASE_MENUS.concat(VALUE_MENUS)
};
const MENUS = PORT_MENUS['8081']; // 兼容旧调用；实际按端口取 PORT_MENUS
// 用 start-all.sh 时 APP_NAME 分别是 bahar-shop/car/food/health，日志落在同目录；
// 但有人在 IDEA 里直接跑、或旧版本用 APP_NAME=bahar 时，零售会落到 /logs/bahar。
// 两个都试，避免因为日志路径猜错就误判"这套跑不起来"。
const LOG_MAP = {
  '8081': ['D:/logs/bahar-shop/server.log', 'D:/logs/bahar/server.log'],
  '8082': ['D:/logs/bahar-car/server.log'],
  '8083': ['D:/logs/bahar-food/server.log'],
  '8084': ['D:/logs/bahar-health/server.log']
};

async function api(base, p, payload, method, token) {
  const headers = { platform: 'PC', 'Content-Type': 'application/json' };
  if (token) { headers['Access-Token'] = token; }
  const res = await fetch(base + p, {
    method: method || 'GET', headers,
    body: payload ? JSON.stringify(payload) : undefined
  });
  return res.json();
}

async function login(base, candidates) {
  const cap = await api(base, '/clientApi/captcha/getCode');
  const uuid = (cap.data || {}).uuid;
  for (const logFile of candidates) {
    if (!fs.existsSync(logFile)) { continue; }
    const re = /生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)/g;
    const txt = fs.readFileSync(logFile, 'utf8');
    let m, code = null;
    while ((m = re.exec(txt)) !== null) {
      if (m[2].trim() === String(uuid).trim()) { code = m[1].trim(); }
    }
    if (!code) { continue; }
    const r = await api(base, '/backendApi/login/doLogin',
      { username: 'bahar', password: '123456', captchaCode: code, uuid }, 'POST');
    if ((r.data || {}).token) { return (r.data || {}).token; }
  }
  throw new Error('读不到验证码: ' + candidates.join(' / '));
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const ports = process.argv.slice(2).length ? process.argv.slice(2)
    : ['8081', '8082', '8083', '8084'];
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--no-proxy-server']
  });
  const bad = [];
  for (const port of ports) {
    const base = 'http://127.0.0.1:' + port;
    let token;
    try {
      token = await login(base, LOG_MAP[port]);
    } catch (e) {
      console.log('端口 ' + port + ' 登录失败: ' + e.message);
      continue;
    }
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push('JS异常: ' + e.message));
    page.on('console', (m) => {
      if (m.type() === 'error') { errs.push('控制台: ' + m.text().slice(0, 80)); }
    });
    await page.goto(base + '/admin/index.html', { waitUntil: 'networkidle2' });
    await page.evaluate((t) => localStorage.setItem('bahar-admin-token', t), token);

    console.log('===== 端口 ' + port + ' =====');
    for (const [route, title] of (PORT_MENUS[String(port)] || MENUS)) {
      errs.length = 0;
      await page.evaluate((r) => { location.hash = '#/' + r; }, route);
      await sleep(2200);
      const info = await page.evaluate(() => ({
        rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length
      }));
      const real = errs.filter((e) => !/favicon/i.test(e));
      const ok = info.rows > 0 && real.length === 0;
      if (!ok) { bad.push(port + ' ' + title); }
      console.log('  ' + (route + '            ').slice(0, 12) + title +
        '  行数=' + info.rows + (ok ? '' : '   <<< ' + (real[0] || '表为空')));
    }
    await page.close();
  }
  await browser.close();
  console.log('===== 汇总: ' + (bad.length
    ? '问题 ' + bad.length + ' 项 -> ' + bad.join(' / ')
    : '全部菜单正常渲染') + ' =====');
})().catch((e) => { console.error('失败: ' + e.message); process.exit(2); });
