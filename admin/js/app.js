/* ==========================================================
 * 应用入口: 路由 + 组件注册 + 启动
 * ========================================================== */
Vue.use(VueRouter);
Vue.use(ELEMENT);
Vue.prototype.$ELEMENT = { size: 'small', zIndex: 3000 };

/* 注册所有业务模块组件 */
adminModules.forEach(function (m) {
  Vue.component(m.key + '-page', makeCrudPage(m.cfg));
});

var routes = [
  { path: '/login', component: LoginPage, meta: { public: true, title: '登录' } },
  {
    path: '/',
    component: AppLayout,
    redirect: '/dashboard',
    children: [{ path: 'dashboard', component: DashboardPage, meta: { title: '首页看板' } }]
      .concat(adminModules.map(function (m) {
        return { path: m.key, component: Vue.component(m.key + '-page'), meta: { title: m.title } };
      }))
  },
  { path: '*', redirect: '/dashboard' }
];

var router = new VueRouter({ mode: 'hash', routes: routes });

router.beforeEach(function (to, from, next) {
  document.title = (to.meta && to.meta.title ? to.meta.title + ' - ' : '') + ADMIN_TITLE;
  if (to.meta && to.meta.public) { next(); return; }
  if (!getToken()) { next('/login'); return; }
  next();
});

window.__baharRouter = router;

new Vue({
  el: '#app',
  router: router,
  template: '<router-view/>'
});
