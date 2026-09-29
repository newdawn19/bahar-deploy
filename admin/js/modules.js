/* ==========================================================
 * 业务模块配置：菜单 + CRUD 契约
 * 所有字段均对应后端实测接口
 * ========================================================== */
function dictSource(url, params) {
  return function () {
    return get(url, Object.assign({ page: 1, pageSize: 200 }, params || {}));
  };
}

var staticDict = {
  goodsType: [
    { label: '实物商品', value: 'goods' },
    { label: '服务项目', value: 'service' },
    { label: '虚拟卡券', value: 'coupon' }
  ],
  yesNo: [{ label: '是', value: 'Y' }, { label: '否', value: 'N' }],
  couponType: [
    { label: '优惠券', value: 'C' },
    { label: '储值卡', value: 'P' },
    { label: '计次卡', value: 'T' }
  ],
  orderStatus: [
    { label: '待付款', value: 'created' },
    { label: '待发货', value: 'payed' },
    { label: '待收货', value: 'delivered' },
    { label: '已完成', value: 'signed' },
    { label: '已取消', value: 'canceled' },
    { label: '退款中', value: 'refunding' },
    { label: '已退款', value: 'refunded' }
  ],
  payStatus: [
    { label: '未支付', value: 'A' },
    { label: '已支付', value: 'B' },
    { label: '已退款', value: 'C' }
  ],
  sex: [{ label: '男', value: 1 }, { label: '女', value: 2 }]
};

/* ---------------- 会员管理 ---------------- */
var memberModule = {
  key: 'member', title: '会员管理', icon: 'el-icon-user',
  cfg: {
    title: '会员',
    list: { method: 'get', url: '/backendApi/member/list' },
    info: { url: '/backendApi/member/info/{id}' },
    save: { url: '/backendApi/member/save' },
    status: { url: '/backendApi/member/updateStatus' },
    del: { method: 'get', url: '/backendApi/member/delete/{id}' },
    dialogWidth: '680px',
    actionWidth: 300,
    dicts: {
      grades: dictSource('/backendApi/userGrade/list'),
      stores: dictSource('/backendApi/store/list'),
      groups: dictSource('/backendApi/member/groupList'),
      statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }]
    },
    queryFields: [
      { label: '会员ID', prop: 'id' },
      { label: '手机号', prop: 'mobile' },
      { label: '名称', prop: 'name' },
      { label: '会员号', prop: 'userNo' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN' }
    ],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '会员号', prop: 'userNo', width: 120 },
      { label: '名称', prop: 'name', width: 120 },
      { label: '手机号', prop: 'mobile', width: 130 },
      { label: '等级', prop: 'gradeId', type: 'dict', dict: 'grades', width: 110 },
      { label: '余额', prop: 'balance', width: 100 },
      { label: '积分', prop: 'point', width: 100 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '名称', prop: 'name', required: true },
      { label: '手机号', prop: 'mobile' },
      { label: '会员等级', prop: 'gradeId', type: 'select', dict: 'grades' },
      { label: '会员号', prop: 'userNo' },
      { label: '性别', prop: 'sex', type: 'select', dict: 'sex' },
      { label: '生日', prop: 'birthday', type: 'date' },
      { label: '地址', prop: 'address' },
      { label: '备注', prop: 'description', type: 'textarea' }
    ],
    rowActions: {
      balance: function (row) {
        var self = this;
        this.$prompt('请输入充值金额（正数充值，负数扣减）', '余额调整',
          { inputPattern: /^-?\d+(\.\d+)?$/, inputErrorMessage: '请输入数字' }).then(function (r) {
          return post('/backendApi/balance/doRecharge', { userId: row.id, amount: parseFloat(r.value) });
        }).then(function () { self.$message.success('操作成功'); self.getList(); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      },
      point: function (row) {
        var self = this;
        this.$prompt('请输入积分变动值（正数增加，负数扣减）', '积分调整',
          { inputPattern: /^-?\d+$/, inputErrorMessage: '请输入整数' }).then(function (r) {
          return post('/backendApi/point/doRecharge', { userId: row.id, point: parseInt(r.value, 10) });
        }).then(function () { self.$message.success('操作成功'); self.getList(); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      },
      resetPwd: function (row) {
        var self = this;
        this.$prompt('请输入新密码', '重置密码', {
          inputValidator: function (v) { return v && v.length >= 6; },
          inputErrorMessage: '密码至少 6 位'
        }).then(function (r) {
          return post('/backendApi/member/resetPwd', { id: row.id, password: r.value });
        }).then(function () { self.$message.success('密码已重置'); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      }
    }
  }
};
memberModule.cfg.rowActions = Object.assign(memberModule.cfg.rowActions, {});
memberModule.cfg.rowActionList = [
  { key: 'balance', label: '余额', icon: 'el-icon-wallet' },
  { key: 'point', label: '积分', icon: 'el-icon-star-off' },
  { key: 'resetPwd', label: '重置密码', icon: 'el-icon-key' }
];

/* ---------------- 会员等级 ---------------- */
var gradeModule = {
  key: 'grade', title: '会员等级', icon: 'el-icon-s-marketing',
  cfg: {
    title: '会员等级',
    list: { method: 'get', url: '/backendApi/userGrade/list' },
    info: { url: '/backendApi/userGrade/info/{id}' },
    save: { url: '/backendApi/userGrade/save' },
    status: { url: '/backendApi/userGrade/updateStatus' },
    del: { method: 'get', url: '/backendApi/userGrade/delete/{id}' },
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '等级值', prop: 'grade', width: 90 },
      { label: '等级名称', prop: 'name', width: 140 },
      { label: '升级条件', prop: 'catchType', width: 120 },
      { label: '达标值', prop: 'catchValue', width: 110 },
      { label: '折扣', prop: 'discount', width: 100 },
      { label: '积分倍率', prop: 'speedPoint', width: 110 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '等级值', prop: 'grade', type: 'int', min: 1 },
      { label: '等级名称', prop: 'name', required: true },
      { label: '达标条件值', prop: 'catchValue', type: 'number', min: 0 },
      { label: '折扣', prop: 'discount', type: 'number', min: 0 },
      { label: '积分倍率', prop: 'speedPoint', type: 'number', min: 0 },
      { label: '等级权益', prop: 'userPrivilege', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 会员分组 ---------------- */
var groupModule = {
  key: 'group', title: '会员分组', icon: 'el-icon-s-grid',
  cfg: {
    title: '会员分组',
    list: { method: 'get', url: '/backendApi/memberGroup/list' },
    info: { url: '/backendApi/memberGroup/info/{id}' },
    save: { url: '/backendApi/memberGroup/save' },
    status: { url: '/backendApi/memberGroup/updateStatus' },
    del: { method: 'get', url: '/backendApi/memberGroup/delete/{id}' },
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '分组名称', prop: 'name', width: 200 },
      { label: '描述', prop: 'description' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '分组名称', prop: 'name', required: true },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 会员标签 ---------------- */
var tagModule = {
  key: 'tag', title: '会员标签', icon: 'el-icon-collection-tag',
  cfg: {
    title: '会员标签',
    list: { method: 'get', url: '/backendApi/userTag/list' },
    save: { url: '/backendApi/userTag/save' },
    del: { method: 'get', url: '/backendApi/userTag/delete/{id}' },
    editable: true,
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '标签名称', prop: 'name', width: 200 },
      { label: '描述', prop: 'description' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '标签名称', prop: 'name', required: true },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 商品分类 ---------------- */
var cateModule = {
  key: 'cate', title: '商品分类', icon: 'el-icon-folder',
  cfg: {
    title: '商品分类',
    list: { method: 'get', url: '/backendApi/goods/cate/list' },
    info: { url: '/backendApi/goods/cate/info/{id}' },
    save: { url: '/backendApi/goods/cate/save' },
    status: { url: '/backendApi/goods/cate/updateStatus' },
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '分类名称', prop: 'name', width: 220 },
      { label: '排序', prop: 'sort', width: 90 },
      { label: '描述', prop: 'description' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '分类名称', prop: 'name', required: true },
      { label: '排序', prop: 'sort', type: 'int', def: 0 },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 商品 / 服务 ---------------- */
var goodsModule = {
  key: 'goods', title: '商品服务', icon: 'el-icon-goods',
  cfg: {
    title: '商品',
    list: { method: 'post', url: '/backendApi/goods/goods/list' },
    info: { url: '/backendApi/goods/goods/info/{id}' },
    save: { url: '/backendApi/goods/goods/save' },
    status: { url: '/backendApi/goods/goods/updateStatus' },
    dialogWidth: '720px',
    dicts: {
      cates: dictSource('/backendApi/goods/cate/list'),
      statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }]
    },
    queryFields: [
      { label: '商品名称', prop: 'name' },
      { label: '商品编号', prop: 'goodsNo' },
      { label: '类型', prop: 'type', type: 'select', dict: 'types' },
      { label: '分类', prop: 'cateId', type: 'select', dict: 'cates' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN' }
    ],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '商品名称', prop: 'name', width: 220 },
      { label: '编号', prop: 'goodsNo', width: 130 },
      { label: '类型', prop: 'type', type: 'dict', dict: 'types', width: 110 },
      { label: '分类', prop: 'cateId', type: 'dict', dict: 'cates', width: 120 },
      { label: '售价', prop: 'price', width: 100 },
      { label: '划线价', prop: 'linePrice', width: 100 },
      { label: '库存', prop: 'stock', width: 90 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '商品名称', prop: 'name', required: true },
      { label: '商品编号', prop: 'goodsNo' },
      { label: '类型', prop: 'type', type: 'select', dict: 'types', def: 'goods' },
      { label: '所属分类', prop: 'cateId', type: 'select', dict: 'cates' },
      { label: '售价', prop: 'price', type: 'number', min: 0 },
      { label: '划线价', prop: 'linePrice', type: 'number', min: 0 },
      { label: '成本价', prop: 'costPrice', type: 'number', min: 0 },
      { label: '库存', prop: 'stock', type: 'number', min: 0, precision: 0 },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    extraDicts: { types: staticDict.goodsType }
  }
};
goodsModule.cfg.dicts.types = staticDict.goodsType;

/* ---------------- 库存流水 ---------------- */
var stockModule = {
  key: 'stock', title: '库存管理', icon: 'el-icon-s-cooperation',
  cfg: {
    title: '库存',
    list: { method: 'get', url: '/backendApi/stock/list' },
    info: { url: '/backendApi/stock/info/{id}' },
    save: { url: '/backendApi/stock/save' },
    del: { method: 'post', url: '/backendApi/stock/delete' },
    editable: false,
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '商品ID', prop: 'goodsId', width: 110 },
      { label: '商品名称', prop: 'goodsName', width: 200 },
      { label: '变动数量', prop: 'num', width: 120 },
      { label: '类型', prop: 'type', width: 120 },
      { label: '备注', prop: 'description' },
      { label: '时间', prop: 'createTime', width: 170 }
    ],
    formFields: []
  }
};

/* ---------------- 卡券管理 ---------------- */
var couponModule = {
  key: 'coupon', title: '卡券管理', icon: 'el-icon-tickets',
  cfg: {
    title: '卡券',
    list: { method: 'get', url: '/backendApi/coupon/list' },
    info: { url: '/backendApi/coupon/info/{id}' },
    save: { url: '/backendApi/coupon/save' },
    del: { method: 'get', url: '/backendApi/coupon/delete/{id}' },
    dialogWidth: '720px',
    dicts: { types: staticDict.couponType },
    queryFields: [
      { label: '卡券名称', prop: 'name' },
      { label: '类型', prop: 'type', type: 'select', dict: 'types' }
    ],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '卡券名称', prop: 'name', width: 200 },
      { label: '类型', prop: 'type', type: 'dict', dict: 'types', width: 110 },
      { label: '面值', prop: 'amount', width: 110 },
      { label: '发放总量', prop: 'total', width: 110 },
      { label: '每人限领', prop: 'limitNum', width: 110 },
      { label: '结束时间', prop: 'endTime', width: 170 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '卡券名称', prop: 'name', required: true },
      { label: '类型', prop: 'type', type: 'select', dict: 'types', def: 'C' },
      { label: '面值/金额', prop: 'amount', type: 'number', min: 0 },
      { label: '发放总量', prop: 'total', type: 'int', min: 0 },
      { label: '每人限领', prop: 'limitNum', type: 'int', min: 0, def: 1 },
      { label: '领取天数', prop: 'expireTime', type: 'int', min: 0 },
      { label: '使用说明', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    rowActions: {
      send: function (row) {
        var self = this;
        this.$prompt('请输入领取会员的手机号（多个用逗号分隔）', '发放卡券').then(function (r) {
          return post('/backendApi/coupon/sendCoupon', { couponId: row.id, mobiles: r.value });
        }).then(function () { self.$message.success('发放成功'); self.getList(); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      }
    }
  }
};
couponModule.cfg.rowActionList = [{ key: 'send', label: '发放', icon: 'el-icon-s-promotion' }];
couponModule.cfg.dicts.statusYN = [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }];

/* ---------------- 会员卡券核销 ---------------- */
var userCouponModule = {
  key: 'userCoupon', title: '卡券核销', icon: 'el-icon-circle-check',
  cfg: {
    title: '会员卡券',
    list: { method: 'get', url: '/backendApi/userCoupon/list' },
    del: { method: 'get', url: '/backendApi/userCoupon/delete/{id}' },
    editable: false,
    actionable: true,
    actionWidth: 160,
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '卡券名称', prop: 'couponName', width: 200 },
      { label: '会员', prop: 'userName', width: 140 },
      { label: '手机号', prop: 'mobile', width: 130 },
      { label: '状态', prop: 'status', width: 100 },
      { label: '领取时间', prop: 'createTime', width: 170 }
    ],
    formFields: [],
    rowActions: {
      confirm: function (row) {
        var self = this;
        this.$confirm('确认核销该卡券？', '核销', { type: 'warning' }).then(function () {
          return get('/backendApi/userCoupon/doConfirm', { id: row.id });
        }).then(function () { self.$message.success('核销成功'); self.getList(); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      }
    }
  }
};
userCouponModule.cfg.rowActionList = [{ key: 'confirm', label: '核销', icon: 'el-icon-check' }];

/* ---------------- 订单管理 ---------------- */
var orderModule = {
  key: 'order', title: '订单管理', icon: 'el-icon-s-order',
  cfg: {
    title: '订单',
    list: { method: 'post', url: '/backendApi/order/list' },
    del: { method: 'get', url: '/backendApi/order/delete/{id}' },
    editable: false,
    actionWidth: 240,
    dicts: { status: staticDict.orderStatus },
    queryFields: [
      { label: '订单号', prop: 'orderSn' },
      { label: '手机号', prop: 'mobile' },
      { label: '订单状态', prop: 'status', type: 'select', dict: 'status' },
      { label: '开始日期', prop: 'startTime', type: 'date' },
      { label: '结束日期', prop: 'endTime', type: 'date' }
    ],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '订单号', prop: 'orderSn', width: 200 },
      { label: '会员', prop: 'userName', width: 130 },
      { label: '手机号', prop: 'mobile', width: 130 },
      { label: '订单金额', prop: 'totalAmount', width: 120 },
      { label: '实付', prop: 'payAmount', width: 110 },
      { label: '状态', prop: 'status', type: 'dict', dict: 'status', width: 110 },
      { label: '支付方式', prop: 'payType', width: 120 },
      { label: '下单时间', prop: 'createTime', width: 170 }
    ],
    formFields: [],
    rowActions: {
      deliver: function (row) {
        var self = this;
        this.$prompt('请输入物流单号', '发货').then(function (r) {
          return post('/backendApi/order/delivered', { orderId: row.id, shippingNo: r.value });
        }).then(function () { self.$message.success('发货成功'); self.getList(); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      },
      detail: function (row) {
        var self = this;
        get('/backendApi/order/info/' + row.id).then(function (body) {
          var d = body.data || {};
          var goods = (d.orderGoodsList || d.orderGoods || []).map(function (g) {
            return (g.goodsName || '-') + ' x ' + (g.num || 1) + '  ¥' + (g.price || 0);
          }).join('<br/>') || '无明细';
          self.$alert('<div><p><b>订单号：</b>' + (d.orderSn || '-') + '</p>' +
            '<p><b>金额：</b>¥' + (d.totalAmount || 0) + '　<b>实付：</b>¥' + (d.payAmount || 0) + '</p>' +
            '<p><b>收货人：</b>' + (d.consignee || '-') + ' ' + (d.phone || '') + '</p>' +
            '<p><b>收货地址：</b>' + (d.address || '-') + '</p>' +
            '<p><b>商品明细：</b><br/>' + goods + '</p></div>', '订单详情', { dangerouslyUseHTMLString: true });
        })['catch'](function (e) { self.$message.error(e.message); });
      }
    }
  }
};
orderModule.cfg.rowActionList = [
  { key: 'detail', label: '详情', icon: 'el-icon-view' },
  { key: 'deliver', label: '发货', icon: 'el-icon-truck' }
];

/* ---------------- 门店管理 ---------------- */
var storeModule = {
  key: 'store', title: '门店管理', icon: 'el-icon-s-shop',
  cfg: {
    title: '门店',
    list: { method: 'get', url: '/backendApi/store/list' },
    info: { url: '/backendApi/store/info/{id}' },
    save: { url: '/backendApi/store/save' },
    status: { url: '/backendApi/store/updateStatus' },
    dialogWidth: '720px',
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] },
    queryFields: [
      { label: '门店名称', prop: 'name' },
      { label: '联系人', prop: 'contact' }
    ],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '门店名称', prop: 'name', width: 200 },
      { label: '联系人', prop: 'contact', width: 120 },
      { label: '联系电话', prop: 'phone', width: 140 },
      { label: '地址', prop: 'address' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '门店名称', prop: 'name', required: true },
      { label: '联系人', prop: 'contact' },
      { label: '联系电话', prop: 'phone' },
      { label: '地址', prop: 'address' },
      { label: '营业时间', prop: 'hours' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ]
  }
};

/* ---------------- 员工管理 ---------------- */
var staffModule = {
  key: 'staff', title: '员工管理', icon: 'el-icon-s-custom',
  cfg: {
    title: '员工',
    list: { method: 'get', url: '/backendApi/staff/list' },
    info: { url: '/backendApi/staff/info/{id}' },
    save: { url: '/backendApi/staff/save' },
    status: { url: '/backendApi/staff/updateStatus' },
    del: { method: 'get', url: '/backendApi/staff/delete/{id}' },
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '姓名', prop: 'realName', width: 140 },
      { label: '手机号', prop: 'mobile', width: 140 },
      { label: '备注', prop: 'description' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '姓名', prop: 'realName', required: true },
      { label: '手机号', prop: 'mobile', required: true },
      { label: '岗位类型', prop: 'category', type: 'int', def: 1 },
      { label: '备注', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 打印机 ---------------- */
var printerModule = {
  key: 'printer', title: '打印设备', icon: 'el-icon-printer',
  cfg: {
    title: '打印机',
    list: { method: 'get', url: '/backendApi/printer/list' },
    info: { url: '/backendApi/printer/info/{id}' },
    save: { url: '/backendApi/printer/save' },
    status: { url: '/backendApi/printer/updateStatus' },
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '设备名称', prop: 'name', width: 200 },
      { label: '设备编号', prop: 'sn', width: 200 },
      { label: '描述', prop: 'description' },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '设备名称', prop: 'name', required: true },
      { label: '设备编号', prop: 'sn' },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 商户信息 ---------------- */
var merchantModule = {
  key: 'merchant', title: '商户信息', icon: 'el-icon-office-building',
  cfg: {
    title: '商户',
    list: { method: 'get', url: '/backendApi/merchant/list' },
    info: { url: '/backendApi/merchant/info/{id}' },
    save: { url: '/backendApi/merchant/save' },
    status: { url: '/backendApi/merchant/updateStatus' },
    editable: true,
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '商户编号', prop: 'no', width: 130 },
      { label: '商户名称', prop: 'name', width: 220 },
      { label: '联系人', prop: 'contact', width: 120 },
      { label: '联系电话', prop: 'phone', width: 140 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '商户名称', prop: 'name', required: true },
      { label: '联系人', prop: 'contact' },
      { label: '联系电话', prop: 'phone' },
      { label: '地址', prop: 'address' },
      { label: '简介', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 文章公告 ---------------- */
var articleModule = {
  key: 'article', title: '文章公告', icon: 'el-icon-document',
  cfg: {
    title: '文章',
    list: { method: 'get', url: '/backendApi/article/list' },
    info: { url: '/backendApi/article/info/{id}' },
    save: { url: '/backendApi/article/save' },
    status: { url: '/backendApi/article/updateStatus' },
    dialogWidth: '720px',
    queryFields: [{ label: '标题', prop: 'title' }],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '标题', prop: 'title', width: 260 },
      { label: '点击量', prop: 'click', width: 100 },
      { label: '排序', prop: 'sort', width: 90 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '标题', prop: 'title', required: true },
      { label: '简介', prop: 'brief', type: 'textarea' },
      { label: '排序', prop: 'sort', type: 'int', def: 0 },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 首页轮播 ---------------- */
var bannerModule = {
  key: 'banner', title: '首页轮播', icon: 'el-icon-picture',
  cfg: {
    title: '轮播',
    list: { method: 'get', url: '/backendApi/banner/list' },
    info: { url: '/backendApi/banner/info/{id}' },
    save: { url: '/backendApi/banner/save' },
    status: { url: '/backendApi/banner/updateStatus' },
    queryFields: [{ label: '标题', prop: 'title' }],
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '标题', prop: 'title', width: 220 },
      { label: '跳转链接', prop: 'url', width: 200 },
      { label: '排序', prop: 'sort', width: 90 },
      { label: '状态', prop: 'status', type: 'tag', width: 90, tagType: "row.status==='A'?'success':'info'" }
    ],
    formFields: [
      { label: '标题', prop: 'title', required: true },
      { label: '跳转链接', prop: 'url' },
      { label: '排序', prop: 'sort', type: 'int', def: 0 },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', type: 'select', dict: 'statusYN', def: 'A' }
    ],
    dicts: { statusYN: [{ label: '启用', value: 'A' }, { label: '停用', value: 'N' }] }
  }
};

/* ---------------- 后台账号 ---------------- */
var accountModule = {
  key: 'account', title: '后台账号', icon: 'el-icon-user-solid',
  cfg: {
    title: '账号',
    list: { method: 'get', url: '/backendApi/account/list' },
    info: { url: '/backendApi/account/info/{userId}' },
    save: { url: '/backendApi/account/doCreate' },
    status: { url: '/backendApi/account/updateStatus' },
    del: { method: 'get', url: '/backendApi/account/delete/{userIds}' },
    dialogWidth: '600px',
    columns: [
      { label: 'ID', prop: 'acctId', width: 80 },
      { label: '账号', prop: 'accountName', width: 160 },
      { label: '姓名', prop: 'realName', width: 140 },
      { label: '创建时间', prop: 'createDate', width: 170 },
      { label: '状态', prop: 'accountStatus', width: 90 }
    ],
    formFields: [
      { label: '账号', prop: 'accountName', required: true },
      { label: '密码', prop: 'password', required: true },
      { label: '姓名', prop: 'realName' }
    ],
    rowActions: {
      resetPwd: function (row) {
        var self = this;
        this.$prompt('请输入新密码', '重置密码', {
          inputValidator: function (v) { return v && v.length >= 6; },
          inputErrorMessage: '密码至少 6 位'
        }).then(function (r) {
          return post('/backendApi/account/resetPwd', { userId: row.acctId, password: r.value });
        }).then(function () { self.$message.success('密码已重置'); })
          ['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      }
    }
  }
};
accountModule.cfg.rowActionList = [{ key: 'resetPwd', label: '重置密码', icon: 'el-icon-key' }];

/* ---------------- 角色职务 ---------------- */
var dutyModule = {
  key: 'duty', title: '角色职务', icon: 'el-icon-s-check',
  cfg: {
    title: '角色',
    list: { method: 'get', url: '/backendApi/duty/list' },
    save: { url: '/backendApi/duty/add' },
    del: { method: 'post', url: '/backendApi/duty/delete/{id}' },
    status: { url: '/backendApi/duty/changeStatus' },
    dialogWidth: '560px',
    columns: [
      { label: 'ID', prop: 'dutyId', width: 80 },
      { label: '角色名称', prop: 'dutyName', width: 200 },
      { label: '描述', prop: 'description' },
      { label: '状态', prop: 'status', width: 90 }
    ],
    formFields: [
      { label: '角色名称', prop: 'dutyName', required: true },
      { label: '描述', prop: 'description', type: 'textarea' },
      { label: '状态', prop: 'status', def: 'A' }
    ]
  }
};

/* ---------------- 操作日志 ---------------- */
var logModule = {
  key: 'actlog', title: '操作日志', icon: 'el-icon-document-copy',
  cfg: {
    title: '日志',
    list: { method: 'get', url: '/backendApi/actlog/list' },
    editable: false,
    columns: [
      { label: 'ID', prop: 'id', width: 80 },
      { label: '操作人', prop: 'operator', width: 140 },
      { label: '操作内容', prop: 'description' },
      { label: 'IP', prop: 'ip', width: 140 },
      { label: '时间', prop: 'createTime', width: 170 }
    ],
    formFields: []
  }
};

/* ================= 菜单树 ================= */
var adminModules = [
  memberModule, gradeModule, groupModule, tagModule,
  cateModule, goodsModule, stockModule,
  couponModule, userCouponModule,
  orderModule,
  storeModule, staffModule, printerModule, merchantModule,
  articleModule, bannerModule,
  accountModule, dutyModule, logModule
];

var adminMenu = [
  {
    title: '会员中心', icon: 'el-icon-user', children: ['member', 'grade', 'group', 'tag']
  },
  {
    title: '商品中心', icon: 'el-icon-goods', children: ['cate', 'goods', 'stock']
  },
  {
    title: '营销卡券', icon: 'el-icon-tickets', children: ['coupon', 'userCoupon']
  },
  {
    title: '交易中心', icon: 'el-icon-s-order', children: ['order']
  },
  {
    title: '门店商户', icon: 'el-icon-s-shop', children: ['store', 'staff', 'printer', 'merchant']
  },
  {
    title: '内容运营', icon: 'el-icon-document', children: ['article', 'banner']
  },
  {
    title: '系统管理', icon: 'el-icon-setting', children: ['account', 'duty', 'actlog']
  }
];
