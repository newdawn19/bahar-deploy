/* ==========================================================
 * bahar Admin —— 极简 i18n 内核（无第三方库）
 * 方案：中文原文当 key，T() 兜底；未翻译文案自动回落中文（不空白）。
 * 加载顺序：必须在 vendor/vue.min.js 之后、api.js 之前引入。
 * ========================================================== */
(function () {
  var LANG_KEY = 'bahar-admin-lang';
  var DICT = {}; // en 词典：{ '中文原文': 'English' }

  // 核心：取文案。lang=zh 直接返回原文；lang=en 命中词典返回译文，否则回落中文。
  function T(s) {
    if (!s) { return s; }
    var lang = localStorage.getItem(LANG_KEY) || 'zh';
    if (lang === 'zh') { return s; }
    return DICT[s] || s;
  }

  // 注入英文词典（由 i18n-en.js 调用）
  function loadEn(obj) { DICT = Object.assign(DICT, obj || {}); }

  function setLang(l) { localStorage.setItem(LANG_KEY, l); }
  function getLang() { return localStorage.getItem(LANG_KEY) || 'zh'; }

  window.BaharI18n = { T: T, loadEn: loadEn, setLang: setLang, getLang: getLang };

  // 让模板表达式可直接访问 T(...) 与 BaharI18n（切换按钮里用到 BaharI18n.getLang/setLang）
  if (typeof Vue !== 'undefined') {
    Vue.prototype.T = T;
    Vue.prototype.BaharI18n = window.BaharI18n;
  }
})();
