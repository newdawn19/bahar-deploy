/* ==========================================================
 * 通用 CRUD 页面组件工厂
 * 所有业务模块页面由 makeCrudPage(cfg) 生成，只需提供列/表单/接口配置
 * ========================================================== */
function makeCrudPage(cfg) {
  return {
    name: cfg.name,
    data: function () {
      var q = {};
      (cfg.queryFields || []).forEach(function (f) {
        q[f.prop] = f.def !== undefined ? f.def : '';
      });
      var form = {};
      (cfg.formFields || []).forEach(function (f) {
        form[f.prop] = f.def !== undefined ? f.def : '';
      });
      return {
        loading: false,
        rows: [],
        total: 0,
        query: Object.assign({ page: 1, pageSize: 10 }, q),
        dialogVisible: false,
        isEdit: false,
        form: form,
        dictMap: {},
        multipleSelection: []
      };
    },
    computed: {
      pageTitle: function () { return cfg.title; }
    },
    created: function () {
      this.loadDicts();
      this.getList();
    },
    methods: {
      /* ---------- 字典 / 下拉数据 ---------- */
      loadDicts: function () {
        var self = this;
        var dicts = cfg.dicts || {};
        Object.keys(dicts).forEach(function (key) {
          var d = dicts[key];
          if (Array.isArray(d)) {
            self.$set(self.dictMap, key, d);
          } else {
            d().then(function (body) {
              // 与列表共用同一套解析，避免字典源换了包装键就变空
              var arr = pickList(body.data).rows;
              self.$set(self.dictMap, key, (arr || []).map(function (i) {
                return { label: i.name || i.dutyName || i.title || i.realName || String(i.id), value: i.id };
              }));
            })['catch'](function () { self.$set(self.dictMap, key, []); });
          }
        });
      },
      dictOf: function (key) { return this.dictMap[key] || []; },
      fmtTime: function (v) { return fmtTime(v); },
      labelOf: function (key, val) {
        var arr = this.dictMap[key] || (cfg.labelMap && cfg.labelMap[key]) || [];
        for (var i = 0; i < arr.length; i++) {
          if (String(arr[i].value) === String(val)) { return arr[i].label; }
        }
        return val === '' || val === null || val === undefined ? '-' : val;
      },

      /* ---------- 列表 ---------- */
      getList: function () {
        var self = this;
        this.loading = true;
        var params = {};
        Object.keys(this.query).forEach(function (k) {
          var v = self.query[k];
          if (v !== '' && v !== null && v !== undefined) { params[k] = v; }
        });
        var p = cfg.list.method === 'post' ? post(cfg.list.url, params) : get(cfg.list.url, params);
        p.then(function (body) {
          var res = pickList(body.data);
          var rows = res.rows;
          var total = res.total;
          // 少数接口后端一个查询参数都不认（实测会员标签、操作日志），
          // 这时退一步在前端按当前页过滤 —— 输入框不能是摆设。
          // 只在当前页生效，所以过滤时把 total 换成实际行数，避免分页器对不上。
          var cf = cfg.clientFilter || [];
          var filtered = false;
          cf.forEach(function (f) {
            var raw = self.query[f];
            var kw = String(raw === undefined || raw === null ? '' : raw).trim();
            if (!kw) { return; }
            filtered = true;
            rows = rows.filter(function (r) {
              var v = r[f];
              return String(v === undefined || v === null ? '' : v).indexOf(kw) >= 0;
            });
          });
          self.rows = rows;
          self.total = filtered ? rows.length : total;
          if (cfg.onLoaded) { cfg.onLoaded.call(self, body.data); }
        })['catch'](function (e) { self.$message.error(e.message); })
          .then(function () { self.loading = false; });
      },
      handleQuery: function () { this.query.page = 1; this.getList(); },
      resetQuery: function () {
        var self = this;
        (cfg.queryFields || []).forEach(function (f) { self.$set(self.query, f.prop, f.def !== undefined ? f.def : ''); });
        this.query.page = 1;
        this.getList();
      },
      handleSizeChange: function (s) { this.query.pageSize = s; this.getList(); },
      handlePageChange: function (p) { this.query.page = p; this.getList(); },
      handleSelectionChange: function (s) { this.multipleSelection = s; },

      /* ---------- 表单 ---------- */
      handleAdd: function () {
        this.isEdit = false;
        this.form = {};
        (cfg.formFields || []).forEach(function (f) { this.form[f.prop] = f.def !== undefined ? f.def : ''; }, this);
        this.dialogVisible = true;
      },
      handleEdit: function (row) {
        var self = this;
        this.isEdit = true;
        if (cfg.info) {
          get(cfg.info.url.replace('{id}', row.id)).then(function (body) {
            self.form = Object.assign({}, body.data || {});
            if (cfg.afterLoad) { cfg.afterLoad.call(self, self.form); }
            self.dialogVisible = true;
          })['catch'](function (e) { self.$message.error(e.message); });
        } else {
          this.form = Object.assign({}, row);
          this.dialogVisible = true;
        }
      },
      submitForm: function () {
        var self = this;
        this.$refs.form.validate(function (valid) {
          if (!valid) { return; }
          var payload = Object.assign({}, self.form);
          if (cfg.beforeSave) { payload = cfg.beforeSave.call(self, payload) || payload; }
          post(cfg.save.url, payload).then(function () {
            self.$message.success(self.isEdit ? '修改成功' : '新增成功');
            self.dialogVisible = false;
            self.getList();
          })['catch'](function (e) { self.$message.error(e.message); });
        });
      },

      /* ---------- 状态 / 删除 ---------- */
      handleStatus: function (row, status) {
        var self = this;
        post(cfg.status.url, { id: row.id, status: status }).then(function () {
          self.$message.success('操作成功');
          self.getList();
        })['catch'](function (e) { self.$message.error(e.message); });
      },
      handleDelete: function (row) {
        var self = this;
        this.$confirm('确认删除该记录？', '提示', { type: 'warning' }).then(function () {
          if (cfg.del.method === 'post') { return post(cfg.del.url, { id: row.id }); }
          return get(cfg.del.url.replace('{id}', row.id));
        }).then(function () {
          self.$message.success('删除成功');
          self.getList();
        })['catch'](function (e) { if (e && e.message) { self.$message.error(e.message); } });
      },
      /* 暴露给自定义行操作使用 */
      callApi: function (method, url, data) {
        if (method === 'get') { return get(url, data); }
        return post(url, data);
      }
    },
    /* 允许各模块自定义方法与行级动作 */
    rowActions: cfg.rowActions || {},
    template: cfg.template || buildTemplate(cfg)
  };
}

/* ---------------- 默认模板生成 ---------------- */
function buildTemplate(cfg) {
  var fields = cfg.formFields || [];
  var cols = cfg.columns || [];

  /* 查询区 */
  var queryHtml = (cfg.queryFields || []).map(function (f) {
    if (f.type === 'select') {
      return '<el-form-item label="' + f.label + '">' +
        '<el-select v-model="query.' + f.prop + '" clearable filterable placeholder="' + f.label + '" style="width:180px">' +
        '<el-option v-for="o in dictOf(\'' + f.dict + '\')" :key="o.value" :label="o.label" :value="o.value"/>' +
        '</el-select></el-form-item>';
    }
    if (f.type === 'date') {
      return '<el-form-item label="' + f.label + '">' +
        '<el-date-picker v-model="query.' + f.prop + '" type="date" value-format="yyyy-MM-dd" placeholder="' + f.label + '" style="width:180px"/>' +
        '</el-form-item>';
    }
    return '<el-form-item label="' + f.label + '">' +
      '<el-input v-model="query.' + f.prop + '" clearable placeholder="请输入' + f.label + '" style="width:180px" @keyup.enter.native="handleQuery"/>' +
      '</el-form-item>';
  }).join('\n');

  /* 至少留一列自适应宽度。
     所有列都写死 width 时 el-table 不会拉伸，表格右侧空出一大块，
     而操作列是 fixed="right" 钉在最右边 —— 看起来就是"状态列和操作列中间断开"
     （会员管理、会员等级、库存这些全宽列的模块都中招；
     会员分组因为有个没写宽度的"描述"列撑开了，所以看着正常）。
     优先挑最后一个没写 type 的普通列放开，用 min-width 保底不至于挤成一条。 */
  var flexIndex = -1;
  cols.forEach(function (c, i) { if (flexIndex < 0 && !c.width) { flexIndex = i; } });
  if (flexIndex < 0 && cols.length) {
    // 挑谁拉伸是有讲究的：优先"名称/地址/描述/接口"这类本来就可能很长的列，
    // 退而求其次才是最后一个普通列。分给"积分""耗时"这种短字段，
    // 拉出来的空白看着还是别扭。
    var picked = -1;
    for (var j = 0; j < cols.length; j++) {
      if (/名称|标题|地址|描述|备注|简介|内容|接口|链接/.test(cols[j].label || '')) { picked = j; break; }
    }
    if (picked < 0) {
      for (var k = cols.length - 1; k >= 0; k--) {
        if (!cols[k].type) { picked = k; break; }
      }
    }
    flexIndex = picked < 0 ? cols.length - 1 : picked;
  }

  /* 表格列 */
  var colHtml = cols.map(function (c, idx) {
    var attrs = 'label="' + c.label + '"';
    if (c.width) {
      attrs += (idx === flexIndex ? ' min-width="' : ' width="') + c.width + '"';
    }
    if (c.prop) { attrs += ' prop="' + c.prop + '"'; }
    if (c.type === 'image') {
      return '<el-table-column ' + attrs + '><template slot-scope="s">' +
        '<img v-if="s.row.' + c.prop + '" :src="' + (c.prefix || '') + ' + s.row.' + c.prop + '" style="max-height:40px;max-width:60px"/>' +
        '<span v-else>-</span></template></el-table-column>';
    }
    if (c.type === 'tag') {
      // 注意: slot-scope 变量名为 s，状态渲染统一按 A=启用 处理
      var valueExpr = "s.row." + c.prop + "==='A'?'启用':'停用'";
      // 兼容历史写法：模块里曾把 tagType 写成 "row.status==='A'?..."，
      // 但模板里的 slot-scope 变量是 s，裸 row 未定义 → Vue 2 渲染时抛
      // "Cannot read property 'status' of undefined"，整张表格渲染中断，
      // 表现就是"接口明明返回了数据，页面却一片空白"。
      // 这里统一补成 s.row.，旧写法也能正常渲染。
      var typeExpr = (c.tagType || "s.row." + c.prop + "==='A'?'success':'info'")
        .replace(/(^|[^.\w$])row\./g, '$1s.row.');
      return '<el-table-column ' + attrs + '><template slot-scope="s">' +
        '<el-tag :type="(' + typeExpr + ')">{{ ' + valueExpr + ' }}</el-tag>' +
        '</template></el-table-column>';
    }
    if (c.type === 'dict') {
      return '<el-table-column ' + attrs + '><template slot-scope="s">{{ labelOf(\'' + c.dict + '\', s.row.' + c.prop + ') }}</template></el-table-column>';
    }
    if (c.type === 'datetime') {
      return '<el-table-column ' + attrs + '><template slot-scope="s">{{ fmtTime(s.row.' + c.prop + ') }}</template></el-table-column>';
    }
    if (c.type === 'switch') {
      return '<el-table-column ' + attrs + '><template slot-scope="s">' +
        '<el-tag :type="s.row.' + c.prop + '===\'A\'?\'success\':\'info\'" v-if="!cfg_statusHidden">' +
        '{{ s.row.' + c.prop + '===\'A\'?\'启用\':\'停用\' }}</el-tag></template></el-table-column>';
    }
    return '<el-table-column ' + attrs + ' :show-overflow-tooltip="true"/>';
  }).join('\n');

  /* 操作列 */
  var actionsHtml = '';
  if (cfg.status || cfg.del || (cfg.rowActions && cfg.rowActions.length) || cfg.editable !== false) {
    var inner = [];
    var btnLabels = [];
    if (cfg.editable !== false) {
      inner.push('<el-button size="mini" type="text" icon="el-icon-edit" @click="handleEdit(scope.row)">编辑</el-button>');
      btnLabels.push('编辑');
    }
    (cfg.rowActionList || []).forEach(function (a) {
      inner.push('<el-button size="mini" type="text" icon="' + (a.icon || 'el-icon-s-tools') + '" @click="rowAction(\'' + a.key + '\', scope.row)">' + a.label + '</el-button>');
      btnLabels.push(a.label || '');
    });
    if (cfg.status) {
      inner.push('<el-button size="mini" type="text" v-if="scope.row.status===\'A\'" @click="handleStatus(scope.row,\'N\')">停用</el-button>');
      inner.push('<el-button size="mini" type="text" v-else @click="handleStatus(scope.row,\'A\')">启用</el-button>');
      btnLabels.push('停用');
    }
    if (cfg.del) {
      inner.push('<el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)">删除</el-button>');
      btnLabels.push('删除');
    }

    // 操作列宽度改成按按钮实际占地估算：写死 220/300 装不下 6 个按钮就会折成两三行，
    // 挤在一格里很乱。估算 = 单元格左右 padding 20
    //             + 每个按钮（icon 16 + 图标间距 4 + 文字 12/字 + 按钮左右 padding 14）
    var est = 20;
    btnLabels.forEach(function (t) { est += 34 + String(t).length * 12; });
    var actionW = Math.max(cfg.actionWidth || 220, est);

    // nowrap 兜底：窗口特别窄宁愿出横向滚动条，也别把按钮折成两行
    actionsHtml = '<el-table-column label="操作" width="' + actionW + '" fixed="right">' +
      '<template slot-scope="scope"><div style="white-space:nowrap">' + inner.join('\n') + '</div></template></el-table-column>';
  }

  /* 表单项 */
  var formHtml = fields.map(function (f) {
    var rules = '';
    if (f.required) { rules = ' :rules="[{required:true,message:\'' + f.label + '不能为空\',trigger:\'blur\'}]"'; }
    var item = '<el-form-item label="' + f.label + '" prop="' + f.prop + '"' + rules + '>';
    if (f.type === 'select') {
      item += '<el-select v-model="form.' + f.prop + '" placeholder="请选择" style="width:100%">' +
        '<el-option v-for="o in dictOf(\'' + f.dict + '\')" :key="o.value" :label="o.label" :value="o.value"/></el-select>';
    } else if (f.type === 'textarea') {
      item += '<el-input type="textarea" :rows="3" v-model="form.' + f.prop + '"/>';
    } else if (f.type === 'number') {
      item += '<el-input-number v-model="form.' + f.prop + '" :min="' + (f.min || 0) + '" :precision="' + (f.precision || 2) + '"/>';
    } else if (f.type === 'int') {
      item += '<el-input-number v-model="form.' + f.prop + '" :min="' + (f.min || 0) + '" :precision="0"/>';
    } else if (f.type === 'date') {
      item += '<el-date-picker v-model="form.' + f.prop + '" type="date" value-format="yyyy-MM-dd" style="width:100%"/>';
    } else if (f.type === 'switch') {
      item += '<el-switch v-model="form.' + f.prop + '" active-value="A" inactive-value="N"/>';
    } else if (f.type === 'readonly') {
      item += '<el-input v-model="form.' + f.prop + '" readonly/>';
    } else {
      item += '<el-input v-model="form.' + f.prop + '" placeholder="请输入' + f.label + '"/>';
    }
    return item + '</el-form-item>';
  }).join('\n');

  return [
    '<div class="app-container">',
    '  <el-form :inline="true" size="small" class="main-search" @submit.native.prevent>',
    queryHtml,
    '    <el-form-item>',
    '      <el-button type="primary" icon="el-icon-search" size="small" @click="handleQuery">搜索</el-button>',
    '      <el-button icon="el-icon-refresh" size="small" @click="resetQuery">重置</el-button>',
    '    </el-form-item>',
    '  </el-form>',
    '  <el-row :gutter="10" class="mb8">',
    '    <el-col :span="1.5"><el-button type="primary" plain icon="el-icon-plus" size="mini" @click="handleAdd">新增</el-button></el-col>',
    '    <el-col :span="1.5"><el-button icon="el-icon-refresh" size="mini" @click="getList">刷新</el-button></el-col>',
    '  </el-row>',
    '  <el-table v-loading="loading" :data="rows" border size="small" @selection-change="handleSelectionChange">',
    colHtml,
    actionsHtml,
    '  </el-table>',
    '  <el-pagination style="margin-top:12px;text-align:right"',
    '    @size-change="handleSizeChange" @current-change="handlePageChange"',
    '    :current-page="query.page" :page-sizes="[10,20,50,100]" :page-size="query.pageSize"',
    '    layout="total, sizes, prev, pager, next, jumper" :total="total"/>',
    '  <el-dialog :title="(isEdit?\'编辑\':\'新增\') + \'' + cfg.title + '\'" :visible.sync="dialogVisible" width="' + (cfg.dialogWidth || '640px') + '" append-to-body>',
    '    <el-form ref="form" :model="form" label-width="110px" size="small">',
    formHtml,
    '    </el-form>',
    '    <div slot="footer"><el-button size="small" @click="dialogVisible=false">取 消</el-button>',
    '      <el-button size="small" type="primary" @click="submitForm">确 定</el-button></div>',
    '  </el-dialog>',
    '</div>'
  ].join('\n');
}

/* 行级自定义动作桥接：由 mixin 注入 */
Vue.mixin({
  methods: {
    rowAction: function (key, row) {
      var actions = (this.$options.rowActions || {});
      if (actions[key]) { actions[key].call(this, row); }
      else { this.$message.info('暂未实现：' + key); }
    }
  }
});
