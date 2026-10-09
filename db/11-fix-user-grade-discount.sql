-- 修复会员等级 DISCOUNT 语义错误（四库通用，幂等）
--
-- 背景：后端把 DISCOUNT 当「折」值用，取值域 0~10（10 = 无折扣）：
--   OrderServiceImpl:459   percent = discount / 10            → 实付比率
--   OrderServiceImpl:2506  memberDiscount = 10 * percent      → 回显给前端的「折」
--   UserGradeServiceImpl:151  discount > 10 || < 0 则报「会员折扣需在0和10之间」
--   pages/user/index.vue:57   买单{{ item.discount }}折
--
-- 而 04-init-basic-data.sql / 00-all-databases.sql 原来播的是 1.00 / 0.98 / 0.95 / 0.90，
-- 那是「比率」不是「折值」，导致：
--   普通会员(1.00) → percent=0.1  → 实付 10%（等于全场 1 折）
--   金卡会员(0.95) → percent=0.095 → 实付 9.5%
-- 修正为：init=10（无折扣）、银卡 9.8 折、金卡 9.5 折、钻石 9 折。

-- 零售
UPDATE `bahar-db`.mt_user_grade       SET DISCOUNT = 10.00 WHERE ID = 1 AND CATCH_TYPE = 'init';
UPDATE `bahar-db`.mt_user_grade       SET DISCOUNT =  9.80 WHERE ID = 2 AND CATCH_TYPE = 'amount';
UPDATE `bahar-db`.mt_user_grade       SET DISCOUNT =  9.50 WHERE ID = 3 AND CATCH_TYPE = 'amount';
UPDATE `bahar-db`.mt_user_grade       SET DISCOUNT =  9.00 WHERE ID = 4 AND CATCH_TYPE = 'amount';

-- 汽车
UPDATE `bahar-car`.mt_user_grade      SET DISCOUNT = 10.00 WHERE ID = 1 AND CATCH_TYPE = 'init';
UPDATE `bahar-car`.mt_user_grade      SET DISCOUNT =  9.80 WHERE ID = 2 AND CATCH_TYPE = 'amount';
UPDATE `bahar-car`.mt_user_grade      SET DISCOUNT =  9.50 WHERE ID = 3 AND CATCH_TYPE = 'amount';
UPDATE `bahar-car`.mt_user_grade      SET DISCOUNT =  9.00 WHERE ID = 4 AND CATCH_TYPE = 'amount';

-- 餐饮
UPDATE `bahar-catering`.mt_user_grade SET DISCOUNT = 10.00 WHERE ID = 1 AND CATCH_TYPE = 'init';
UPDATE `bahar-catering`.mt_user_grade SET DISCOUNT =  9.80 WHERE ID = 2 AND CATCH_TYPE = 'amount';
UPDATE `bahar-catering`.mt_user_grade SET DISCOUNT =  9.50 WHERE ID = 3 AND CATCH_TYPE = 'amount';
UPDATE `bahar-catering`.mt_user_grade SET DISCOUNT =  9.00 WHERE ID = 4 AND CATCH_TYPE = 'amount';

-- 康养
UPDATE `bahar-health`.mt_user_grade   SET DISCOUNT = 10.00 WHERE ID = 1 AND CATCH_TYPE = 'init';
UPDATE `bahar-health`.mt_user_grade   SET DISCOUNT =  9.80 WHERE ID = 2 AND CATCH_TYPE = 'amount';
UPDATE `bahar-health`.mt_user_grade   SET DISCOUNT =  9.50 WHERE ID = 3 AND CATCH_TYPE = 'amount';
UPDATE `bahar-health`.mt_user_grade   SET DISCOUNT =  9.00 WHERE ID = 4 AND CATCH_TYPE = 'amount';
