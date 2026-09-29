/* ==========================================================
 * 登录页 + 首页看板 + 外层框架布局
 * ========================================================== */

/* ---------------- 登录页 ---------------- */
var LoginPage = {
  name: 'LoginPage',
  data: function () {
    return {
      loading: false,
      captchaImage: '',
      form: { username: 'bahar', password: '', captchaCode: '', uuid: '' }
    };
  },
  mounted: function () { this.refreshCaptcha(); },
  methods: {
    refreshCaptcha: function () {
      var self = this;
      authApi.captcha().then(function (body) {
        self.captchaImage = body.data.image;
        self.form.uuid = body.data.uuid;
      })['catch'](function (e) { self.$message.error(e.message); });
    },
    doLogin: function () {
      var self = this;
      if (!this.form.username || !this.form.password) {
        this.$message.warning('请输入账号和密码'); return;
      }
      if (!this.form.captchaCode) { this.$message.warning('请输入验证码'); return; }
      this.loading = true;
      authApi.login(this.form).then(function (body) {
        setToken(body.data.token);
        return authApi.getInfo();
      }).then(function (body) {
        setStoredUser(body.data.accountInfo || {});
        self.$message.success('登录成功');
        window.__baharRouter.push('/');
      })['catch'](function (e) {
        self.$message.error(e.message);
        self.refreshCaptcha();
      }).then(function () { self.loading = false; });
    }
  },
  template: [
    '<div class="login-wrap">',
    '  <div class="login-box">',
    '    <h2 class="login-title">{{ adminTitle }}</h2>',
    '    <p class="login-sub">会员营销管理系统 · 管理后台</p>',
    '    <el-form size="medium" @submit.native.prevent>',
    '      <el-form-item><el-input v-model="form.username" prefix-icon="el-icon-user" placeholder="请输入账号"/></el-form-item>',
    '      <el-form-item><el-input v-model="form.password" type="password" prefix-icon="el-icon-lock" placeholder="请输入密码" @keyup.enter.native="doLogin"/></el-form-item>',
    '      <el-form-item>',
    '        <el-row :gutter="10">',
    '          <el-col :span="14"><el-input v-model="form.captchaCode" placeholder="验证码"/></el-col>',
    '          <el-col :span="10"><img class="cap-img" v-if="captchaImage" :src="captchaImage" @click="refreshCaptcha" title="点击刷新"/></el-col>',
    '        </el-row>',
    '      </el-form-item>',
    '      <el-button type="primary" style="width:100%" :loading="loading" @click="doLogin">登 录</el-button>',
    '    </el-form>',
    '    <p class="login-tip">演示账号 bahar / 123456 （验证码不区分大小写）</p>',
    '  </div>',
    '</div>'
  ].join('\n'),
  computed: {
    adminTitle: function () { return ADMIN_TITLE; }
  }
};

/* ---------------- 首页看板 ---------------- */
var DashboardPage = {
  name: 'DashboardPage',
  data: function () {
    return {
      loading: true,
      cards: [
        { key: 'member', label: '会员总数', value: '-', icon: 'el-icon-user', color: '#409EFF' },
        { key: 'order', label: '订单总数', value: '-', icon: 'el-icon-s-order', color: '#67C23A' },
        { key: 'amount', label: '累计销售额', value: '-', icon: 'el-icon-money', color: '#E6A23C' },
        { key: 'today', label: '今日订单', value: '-', icon: 'el-icon-data-line', color: '#F56C6C' }
      ],
      topRows: [],
      memberRows: []
    };
  },
  mounted: function () { this.load(); },
  methods: {
    load: function () {
      var self = this;
      this.loading = true;
      authApi.getInfo()['catch'](function () { return { data: {} }; });
      // 会员总数
      homeApi.totalMember().then(function (body) {
        self.setCard('member', self.pickNum(body.data));
      })['catch'](function () { });

      // 首页聚合统计
      homeApi.statistic().then(function (body) {
        var d = body.data || {};
        if (d.orderCount !== undefined) { self.setCard('order', d.orderCount); }
        if (d.totalAmount !== undefined) { self.setCard('amount', '¥' + (d.totalAmount || 0)); }
        if (d.todayOrderCount !== undefined) { self.setCard('today', d.todayOrderCount); }
      })['catch'](function () { });

      // 热销排行
      homeApi.top({}).then(function (body) {
        var r = pickList(body.data);
        self.topRows = r.rows.slice(0, 10);
      })['catch'](function () { }).then(function () { self.loading = false; });

      // 最新会员
      get('/backendApi/member/list', { page: 1, pageSize: 6 }).then(function (body) {
        self.memberRows = pickList(body.data).rows;
      })['catch'](function () { });
    },
    setCard: function (key, val) {
      for (var i = 0; i < this.cards.length; i++) {
        if (this.cards[i].key === key) { this.$set(this.cards, i, Object.assign({}, this.cards[i], { value: val })); }
      }
    },
    pickNum: function (data) {
      if (data === null || data === undefined) { return '-'; }
      if (typeof data === 'object') {
        return (data.total !== undefined ? data.total :
          (data.totalMember !== undefined ? data.totalMember : '-'));
      }
      return data;
    }
  },
  template: [
    '<div class="app-container" v-loading="loading">',
    '  <el-row :gutter="16">',
    '    <el-col :span="6" v-for="c in cards" :key="c.key">',
    '      <el-card shadow="hover" class="stat-card">',
    '        <div class="stat-icon" :style="{background:c.color}"><i :class="c.icon"/></div>',
    '        <div class="stat-body"><div class="stat-label">{{ c.label }}</div>',
    '        <div class="stat-value">{{ c.value }}</div></div>',
    '      </el-card>',
    '    </el-col>',
    '  </el-row>',
    '  <el-row :gutter="16" style="margin-top:16px">',
    '    <el-col :span="12">',
    '      <el-card shadow="hover" header="热销排行 Top10">',
    '        <el-table :data="topRows" size="mini" max-height="320">',
    '          <el-table-column label="名称" prop="name" :show-overflow-tooltip="true"/>',
    '          <el-table-column label="销量" prop="num" width="90"/>',
    '          <el-table-column label="金额" prop="amount" width="110"/>',
    '        </el-table>',
    '        <p v-if="!topRows.length" class="empty-tip">暂无数据</p>',
    '      </el-card>',
    '    </el-col>',
    '    <el-col :span="12">',
    '      <el-card shadow="hover" header="最新会员">',
    '        <el-table :data="memberRows" size="mini" max-height="320">',
    '          <el-table-column label="名称" prop="name" width="120"/>',
    '          <el-table-column label="手机号" prop="mobile" width="130"/>',
    '          <el-table-column label="余额" prop="balance" width="100"/>',
    '          <el-table-column label="积分" prop="point" width="100"/>',
    '        </el-table>',
    '        <p v-if="!memberRows.length" class="empty-tip">暂无数据</p>',
    '      </el-card>',
    '    </el-col>',
    '  </el-row>',
    '</div>'
  ].join('\n')
};

/* ---------------- 框架布局 ---------------- */
var AppLayout = {
  name: 'AppLayout',
  data: function () {
    return { menus: adminMenu, modMap: {}, collapsed: false };
  },
  computed: {
    adminTitle: function () { return ADMIN_TITLE; },
    userName: function () {
      var u = getStoredUser();
      return u.accountName || u.realName || '管理员';
    },
    activePath: function () { return this.$route.path; }
  },
  created: function () {
    var map = {};
    adminModules.forEach(function (m) { map[m.key] = m; });
    this.modMap = map;
  },
  methods: {
    titleOf: function (key) { return this.modMap[key] ? this.modMap[key].title : key; },
    iconOf: function (key) { return this.modMap[key] ? this.modMap[key].icon : 'el-icon-menu'; },
    logout: function () {
      var self = this;
      authApi.logout()['catch'](function () { }).then(function () {
        removeToken();
        window.__baharRouter.push('/login');
        self.$message.success('已退出登录');
      });
    }
  },
  template: [
    '<el-container class="layout-wrap">',
    '  <el-aside :width="collapsed?\'64px\':\'210px\'" class="layout-aside">',
    '    <div class="brand"><i class="el-icon-s-platform"/> <span v-show="!collapsed">{{ adminTitle }}</span></div>',
    '    <el-menu :default-active="activePath" :collapse="collapsed" unique-opened background-color="#001529"',
    '             text-color="#bfcbd9" active-text-color="#409EFF" router>',
    '      <el-menu-item index="/dashboard"><i class="el-icon-data-line"/><span slot="title">首页看板</span></el-menu-item>',
    '      <el-submenu v-for="g in menus" :key="g.title" :index="g.title">',
    '        <template slot="title"><i :class="g.icon"/><span>{{ g.title }}</span></template>',
    '        <el-menu-item v-for="c in g.children" :key="c" :index="\'/\'+c">',
    '          <i :class="iconOf(c)"/><span slot="title">{{ titleOf(c) }}</span>',
    '        </el-menu-item>',
    '      </el-submenu>',
    '    </el-menu>',
    '  </el-aside>',
    '  <el-container>',
    '    <el-header class="layout-header">',
    '      <i :class="collapsed?\'el-icon-s-unfold\':\'el-icon-s-fold\'" class="collapse-btn" @click="collapsed=!collapsed"/>',
    '      <div class="header-title">{{ $route.meta.title || \'\' }}</div>',
    '      <div class="header-right">',
    '        <span class="user-name"><i class="el-icon-user"/> {{ userName }}</span>',
    '        <el-button type="text" icon="el-icon-switch-button" @click="logout">退出</el-button>',
    '      </div>',
    '    </el-header>',
    '    <el-main class="layout-main">',
    '      <router-view/>',
    '    </el-main>',
    '  </el-container>',
    '</el-container>'
  ].join('\n')
};
