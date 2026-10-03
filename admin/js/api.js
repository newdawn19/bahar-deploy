/* ==========================================================
 * bahar Admin —— 通用请求层
 * 约定来源（源码实测）：
 *   - 响应信封: { code, message, data }，成功码 200
 *   - 鉴权头:   Access-Token
 *   - 未登录:   code 1001 / 1003
 *   - 分页返回: data.paginationResponse.{content,totalElements}
 * ========================================================== */
var ADMIN_TITLE = window.__BAHAR_ADMIN_TITLE__ || 'bahar 会员营销管理系统';
var BASE_URL = window.__BAHAR_ADMIN_BASE__ || '';

var TOKEN_KEY = 'bahar-admin-token';
var USER_KEY = 'bahar-admin-user';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function removeToken() { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); }
function getStoredUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || '{}'); } catch (e) { return {}; }
}
function setStoredUser(u) { localStorage.setItem(USER_KEY, JSON.stringify(u || {})); }

var http = axios.create({ baseURL: BASE_URL, timeout: 30000 });

http.interceptors.request.use(function (config) {
  var t = getToken();
  if (t) { config.headers['Access-Token'] = t; }
  return config;
});

// 统一拆信封 + 异常处理
function unwrap(promise) {
  return promise.then(function (res) {
    var body = res.data || {};
    if (body.code === 200) { return body; }
    if (body.code === 1001 || body.code === 1003) {
      removeToken();
      if (window.__baharRouter && window.__baharRouter.currentRoute.path !== '/login') {
        window.__baharRouter.push('/login');
      }
      throw new Error(body.message || '登录已失效，请重新登录');
    }
    throw new Error(body.message || ('请求失败(' + body.code + ')'));
  });
}

function req(method, url, params, data) {
  return unwrap(http({ method: method, url: url, params: params, data: data }));
}
function get(url, params) { return req('get', url, params); }
function post(url, data, params) { return req('post', url, params, data); }

/* ------------------ 登录 / 权限 ------------------ */
var authApi = {
  captcha: function () { return get('/backendApi/captcha/getLoginCode'); },
  login: function (d) { return post('/backendApi/login/doLogin', d); },
  getInfo: function () { return get('/backendApi/login/getInfo'); },
  logout: function () { return post('/backendApi/login/logout'); }
};

/* ------------------ 首页统计 ------------------ */
var homeApi = {
  index: function () { return get('/backendApi/home/index'); },
  statistic: function () { return get('/backendApi/home/statistic'); },
  totalMember: function () { return get('/backendApi/statistic/totalMember'); },
  main: function (p) { return post('/backendApi/statistic/main', p || {}); },
  top: function (p) { return post('/backendApi/statistic/top', p || {}); }
};

/* ------------------ 请求方法自适应 ------------------
 * 四套工程的同名接口存在 GET/POST 不一致（例如商品列表：
 * 零售/汽车/康养是 POST，餐饮是 GET），而 Admin 是四实例共用同一份静态资源。
 * 因此：按配置方法发起，若服务端报 "method not supported"，自动换另一种方法重试，
 * 并把成功的方法写进 localStorage，后续请求直接命中。
 * ---------------------------------------------------- */
var METHOD_CACHE_KEY = 'bahar-admin-methods';

function getMethodCache() {
  try { return JSON.parse(localStorage.getItem(METHOD_CACHE_KEY) || '{}'); } catch (e) { return {}; }
}
function setMethodCache(url, m) {
  try {
    var c = getMethodCache();
    c[url] = m;
    localStorage.setItem(METHOD_CACHE_KEY, JSON.stringify(c));
  } catch (e) { /* 忽略：localStorage 不可用时退化为每次探测 */ }
}
function isMethodUnsupported(err) {
  var msg = (err && err.message) || '';
  // 两种形态都见过：
  //   1) 被 @RestControllerAdvice 接住 -> HTTP 200 + code 201，
  //      message 是 Spring 原话 "Request method 'POST' not supported"，
  //      或工程自己包装的 "请求地址'...',不支持'POST'请求"
  //   2) 没被接住直接冒泡 -> axios 抛 "Request failed with status code 405"
  // 注意别只匹配"不支持"两个字：业务异常里也常有"该操作不支持"，
  // 认错会白跑一次重试、还把真正的报错盖过去。
  return /not supported|不支持.{0,10}(请求|方式|方法)|method not allowed|status code 405/i.test(msg);
}
// 用另一种方法兜底重试。preferred 只是"首选"，命中过的方法记在缓存里优先用。
function callWithFallback(url, preferred, params) {
  var first = getMethodCache()[url] || (preferred === 'post' ? 'post' : 'get');
  function call(m) {
    var p = (m === 'post') ? post(url, params) : get(url, params);
    return p.then(function (r) { setMethodCache(url, m); return r; });
  }
  return call(first)['catch'](function (e) {
    if (!isMethodUnsupported(e)) { throw e; }
    return call(first === 'post' ? 'get' : 'post');
  });
}

/* ------------------ 通用 CRUD 工厂 ------------------ */
// cfg: { list: {method,url}, save:url, info:url, status:url, del:url, ... }
function crudApi(cfg) {
  var api = {};
  if (cfg.list) {
    api.list = function (params) {
      return callWithFallback(cfg.list.url, cfg.list.method, params);
    };
  }
  if (cfg.info) { api.info = function (id) { return get(cfg.info.url.replace('{id}', id)); }; }
  if (cfg.save) { api.save = function (d) { return post(cfg.save.url, d); }; }
  if (cfg.status) { api.status = function (id, status) { return post(cfg.status.url, { id: id, status: status }); }; }
  if (cfg.del) {
    api.del = function (id) {
      if (cfg.del.method === 'post') { return post(cfg.del.url, { id: id }); }
      return get(cfg.del.url.replace('{id}', id));
    };
  }
  if (cfg.extra) { for (var k in cfg.extra) { api[k] = cfg.extra[k]; } }
  return api;
}

/* 时间戳格式化：后端时间字段一会儿是毫秒数（createTime/actionTime），
   一会儿是字符串（createDate）。直接把 1790479560000 打到表格里没人看得懂，
   列配置里写 type:'datetime' 就会走这里。 */
function fmtTime(v) {
  if (v === null || v === undefined || v === '') { return '-'; }
  var d = null;
  if (typeof v === 'number') { d = new Date(v); }
  else if (typeof v === 'string' && /^\d+$/.test(v)) { d = new Date(parseInt(v, 10)); }
  else { return v; }
  if (isNaN(d.getTime())) { return v; }
  function p(n) { return n < 10 ? '0' + n : '' + n; }
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
}

/* 取列表数据：后端包装键不统一，这里尽量兼容。
 * 见过的形态：
 *   data.paginationResponse.{content,totalElements}   会员/商品/门店/订单……
 *   data.dataList.{content,totalElements}             商户/文章/轮播
 *   data.{content,totalElements}                      账号/职务/操作日志
 *   data.list                                         会员标签
 *   data 本身是数组                                    少数接口
 * 最后一轮兜底遍历一遍 data 的值：只要里面藏着带 content 的分页对象就取出来。
 * 目的很实在 —— 少认一种形态，页面上就是一个"接口有数据、表格一片空白"的坑。 */
function isArray(v) { return Object.prototype.toString.call(v) === '[object Array]'; }

function pickPage(v) {
  if (!v) { return null; }
  if (isArray(v)) { return { rows: v, total: v.length }; }
  if (isArray(v.content)) {
    return { rows: v.content, total: v.totalElements || v.content.length };
  }
  return null;
}

function pickList(data) {
  if (!data) { return { rows: [], total: 0 }; }
  if (isArray(data)) { return { rows: data, total: data.length }; }

  var hit = pickPage(data.paginationResponse) || pickPage(data.dataList);
  if (hit) { return hit; }

  hit = pickPage(data);
  if (hit) { return hit; }

  if (isArray(data.list)) { return { rows: data.list, total: data.total || data.list.length }; }

  for (var k in data) {
    if (!Object.prototype.hasOwnProperty.call(data, k)) { continue; }
    hit = pickPage(data[k]);
    if (hit) { return hit; }
  }
  return { rows: [], total: 0 };
}
