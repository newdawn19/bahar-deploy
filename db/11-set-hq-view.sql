-- 演示账号改「总部 + 平台」视角：门店只 1 家、商户只 1 条 → 各 3 条全可见
--
-- 原因：t_account.merchant_id / store_id 会写进登录态，后台几乎所有列表接口
-- 都按它们过滤。看两个控制器就很清楚：
--
--   BackendStoreController.list   : storeId    > 0 -> eq 门店
--   BackendMerchantController.list: merchantId > 0 -> setId(商户ID)
--
-- 演示账号原本绑 merchant_id=1 / store_id=1，于是：
--   门店管理只剩 1 条（演示总店，两家分店看不见）
--   商户信息只剩 1 条（自己的商户，后补的商户看不见）
--   其余菜单的条数也被这一家店的数据限制住，看上去像"没灌数据"
--
-- 改成 0 后走「不加过滤」分支，3 家店 + 3 个商户的数据全部可见。
-- 实测（四库 × 19 菜单）：条数只增不减，无回归 ——
--   门店 1 -> 3、商户 1 -> 3；商品 43-44 / 会员 60 / 订单 80 等均保持不变
--
-- 想还原成单店视角：UPDATE t_account SET merchant_id = 1, store_id = 1 WHERE acct_id = 1;

UPDATE t_account SET merchant_id = 0, store_id = 0 WHERE acct_id = 1;
