-- ============================================================
-- 新增列的存量数据回填
-- 背景：deploy/db/05-entity-sync-tool.py 补齐了实体缺失列，
--       但存量行在这些列上全是 NULL；而代码里大量使用
--       wrapper.eq(MtUser::getIsStaff, 'N') 之类的等值过滤，
--       NULL 会导致查不到数据（如会员列表返回 0 条）。
-- 本脚本幂等，只回填 IS NULL 的行，可重复执行。
-- ============================================================

-- ---------- mt_user.is_staff（四库）----------
UPDATE `bahar-db`.`mt_user`       SET is_staff = 'N' WHERE is_staff IS NULL;
UPDATE `bahar-car`.`mt_user`      SET is_staff = 'N' WHERE is_staff IS NULL;
UPDATE `bahar-catering`.`mt_user` SET is_staff = 'N' WHERE is_staff IS NULL;
UPDATE `bahar-health`.`mt_user`   SET is_staff = 'N' WHERE is_staff IS NULL;

-- ---------- mt_user.profile_completed（四库，N=资料未完善）----------
UPDATE `bahar-db`.`mt_user`       SET profile_completed = 'N' WHERE profile_completed IS NULL;
UPDATE `bahar-car`.`mt_user`      SET profile_completed = 'N' WHERE profile_completed IS NULL;
UPDATE `bahar-catering`.`mt_user` SET profile_completed = 'N' WHERE profile_completed IS NULL;
UPDATE `bahar-health`.`mt_user`   SET profile_completed = 'N' WHERE profile_completed IS NULL;

-- ---------- mt_user.is_rider（餐饮，N=非骑手）----------
UPDATE `bahar-catering`.`mt_user` SET is_rider = 'N' WHERE is_rider IS NULL;

-- ---------- mt_goods.platform（餐饮：0=不限平台）----------
UPDATE `bahar-catering`.`mt_goods` SET platform = '0' WHERE platform IS NULL;
UPDATE `bahar-car`.`mt_goods`      SET platform = '0' WHERE platform IS NULL;

-- ---------- mt_table.use_status（餐饮：N=空闲）----------
UPDATE `bahar-catering`.`mt_table` SET use_status = 'N' WHERE use_status IS NULL;

-- ---------- mt_printer.type / before_pay / after_pay（餐饮）----------
UPDATE `bahar-catering`.`mt_printer` SET type = '0'      WHERE type IS NULL;
UPDATE `bahar-catering`.`mt_printer` SET before_pay = 'N' WHERE before_pay IS NULL;
UPDATE `bahar-catering`.`mt_printer` SET after_pay  = 'N' WHERE after_pay IS NULL;

-- ---------- mt_merchant.settle_rate / 有效期（四库）----------
UPDATE `bahar-db`.`mt_merchant`       SET settle_rate = 0.00 WHERE settle_rate IS NULL;
UPDATE `bahar-car`.`mt_merchant`      SET settle_rate = 0.00 WHERE settle_rate IS NULL;
UPDATE `bahar-catering`.`mt_merchant` SET settle_rate = 0.00 WHERE settle_rate IS NULL;
UPDATE `bahar-health`.`mt_merchant`   SET settle_rate = 0.00 WHERE settle_rate IS NULL;

-- ---------- mt_user_grade.rebate（返利比例）----------
-- 注意：餐饮版 MtUserGrade 实体不含 rebate 字段，故跳过
UPDATE `bahar-db`.`mt_user_grade`     SET rebate = 0 WHERE rebate IS NULL;
UPDATE `bahar-car`.`mt_user_grade`    SET rebate = 0 WHERE rebate IS NULL;
UPDATE `bahar-health`.`mt_user_grade` SET rebate = 0 WHERE rebate IS NULL;

-- ---------- 校验 ----------
SELECT 'bahar-db' db, SUM(is_staff IS NULL) is_staff_null, SUM(profile_completed IS NULL) pc_null
FROM `bahar-db`.`mt_user`
UNION ALL SELECT 'bahar-car',      SUM(is_staff IS NULL), SUM(profile_completed IS NULL) FROM `bahar-car`.`mt_user`
UNION ALL SELECT 'bahar-catering', SUM(is_staff IS NULL), SUM(profile_completed IS NULL) FROM `bahar-catering`.`mt_user`
UNION ALL SELECT 'bahar-health',   SUM(is_staff IS NULL), SUM(profile_completed IS NULL) FROM `bahar-health`.`mt_user`;
