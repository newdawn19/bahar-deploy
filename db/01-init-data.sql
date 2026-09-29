-- ============================================================
-- bahar 演示环境 —— 最小初始化数据（幂等，可重复执行）
-- 生成时间: 2026-09-27
--
-- 后台登录账号: bahar / 123456
-- 密码算法: SHA1(salt_bytes || password_bytes) 迭代 1024 次, hex 存储
--   salt     = 1a2b3c4d5e6f7a8b
--   password = b380f7a1afe140f323a3528a0fd709c65e65e2a1
--
-- 安全说明:
--   1. 本脚本只 INSERT 固定 ID 的演示数据，不 DROP / 不 DELETE 业务数据
--   2. 每次执行前先按固定 ID 清理自己的记录，可安全重复执行
--   3. 商户编号固定为 10001（与 baharUniapp/config.js 的 merchantNo 一致）
-- ============================================================

-- ############################################################
-- 1) bahar-db  （主系统 bahar）
-- ############################################################
USE `bahar-db`;

DELETE FROM t_account_duty WHERE acc_duty_id = 1;
DELETE FROM t_account WHERE acct_id = 1;
DELETE FROM t_duty WHERE duty_id = 1;
DELETE FROM mt_store WHERE ID = 1;
DELETE FROM mt_merchant WHERE ID = 1;
DELETE FROM t_platform WHERE owner_id = 1;

INSERT INTO t_platform (owner_id, name, status, description, platform_type)
VALUES (1, 'bahar演示平台', 1, '演示环境平台方', 1);

INSERT INTO mt_merchant (ID, TYPE, NO, NAME, CONTACT, PHONE, ADDRESS, DESCRIPTION,
                         CREATE_TIME, UPDATE_TIME, START_TIME, END_TIME, STATUS, OPERATOR)
VALUES (1, 'MERCHANT', '10001', '演示商户', '演示联系人', '13800138000', '演示地址',
        'bahar 演示环境商户', NOW(), NOW(), '2020-01-01 00:00:00', '2030-12-31 23:59:59', 'A', 'system');

INSERT INTO mt_store (ID, MERCHANT_ID, NAME, IS_DEFAULT, CONTACT, PHONE, ADDRESS,
                      CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 1, '演示总店', 'Y', '演示联系人', '13800138000', '演示地址', NOW(), NOW(), 'A', 'system');

INSERT INTO t_duty (duty_id, merchant_id, duty_name, status, description, duty_type)
VALUES (1, 1, '超级管理员', 'A', '演示环境内置超级管理员', 'SYSTEM');

INSERT INTO t_account (acct_id, account_key, account_name, password, account_status, is_active,
                       create_date, modify_date, salt, role_ids, locked, owner_id,
                       real_name, merchant_id, store_id, staff_id)
VALUES (1, 'demo-key-0000000001', 'bahar', 'b380f7a1afe140f323a3528a0fd709c65e65e2a1',
        1, 1, NOW(), NOW(), '1a2b3c4d5e6f7a8b', '1', 0, 1, '演示管理员', 1, 1, 0);

INSERT INTO t_account_duty (acc_duty_id, acct_id, duty_id) VALUES (1, 1, 1);

-- ############################################################
-- 2) bahar-car  （汽车美容 baharCar）
-- ############################################################
USE `bahar-car`;

DELETE FROM t_account_duty WHERE acc_duty_id = 1;
DELETE FROM t_account WHERE acct_id = 1;
DELETE FROM t_duty WHERE duty_id = 1;
DELETE FROM mt_store WHERE ID = 1;
DELETE FROM mt_merchant WHERE ID = 1;
DELETE FROM t_platform WHERE owner_id = 1;

INSERT INTO t_platform (owner_id, name, status, description, platform_type)
VALUES (1, 'bahar演示平台', 1, '演示环境平台方', 1);

-- 注意: bahar-car 的 mt_merchant 无 START_TIME/END_TIME 列（有效期为空视为永久有效）
INSERT INTO mt_merchant (ID, TYPE, NO, NAME, CONTACT, PHONE, ADDRESS, DESCRIPTION,
                         CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 'MERCHANT', '10001', '演示汽车服务门店', '演示联系人', '13800138000', '演示地址',
        'baharCar 演示环境商户', NOW(), NOW(), 'A', 'system');

INSERT INTO mt_store (ID, MERCHANT_ID, NAME, IS_DEFAULT, CONTACT, PHONE, ADDRESS,
                      CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 1, '演示汽车总店', 'Y', '演示联系人', '13800138000', '演示地址', NOW(), NOW(), 'A', 'system');

INSERT INTO t_duty (duty_id, merchant_id, duty_name, status, description, duty_type)
VALUES (1, 1, '超级管理员', 'A', '演示环境内置超级管理员', 'SYSTEM');

INSERT INTO t_account (acct_id, account_key, account_name, password, account_status, is_active,
                       create_date, modify_date, salt, role_ids, locked, owner_id,
                       real_name, merchant_id, store_id, staff_id)
VALUES (1, 'demo-key-0000000001', 'bahar', 'b380f7a1afe140f323a3528a0fd709c65e65e2a1',
        1, 1, NOW(), NOW(), '1a2b3c4d5e6f7a8b', '1', 0, 1, '演示管理员', 1, 1, 0);

INSERT INTO t_account_duty (acc_duty_id, acct_id, duty_id) VALUES (1, 1, 1);

-- ############################################################
-- 3) bahar-catering  （餐饮 baharCatering）
-- ############################################################
USE `bahar-catering`;

DELETE FROM t_account_duty WHERE acc_duty_id = 1;
DELETE FROM t_account WHERE acct_id = 1;
DELETE FROM t_duty WHERE duty_id = 1;
DELETE FROM mt_store WHERE ID = 1;
DELETE FROM mt_merchant WHERE ID = 1;
DELETE FROM t_platform WHERE owner_id = 1;

INSERT INTO t_platform (owner_id, name, status, description, platform_type)
VALUES (1, 'bahar演示平台', 1, '演示环境平台方', 1);

-- 注意: bahar-food 的 mt_merchant 无 START_TIME/END_TIME 列（有效期为空视为永久有效）
INSERT INTO mt_merchant (ID, TYPE, NO, NAME, CONTACT, PHONE, ADDRESS, DESCRIPTION,
                         CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 'MERCHANT', '10001', '演示餐饮门店', '演示联系人', '13800138000', '演示地址',
        'baharCatering 演示环境商户', NOW(), NOW(), 'A', 'system');

INSERT INTO mt_store (ID, MERCHANT_ID, NAME, IS_DEFAULT, CONTACT, PHONE, ADDRESS,
                      CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 1, '演示餐饮总店', 'Y', '演示联系人', '13800138000', '演示地址', NOW(), NOW(), 'A', 'system');

INSERT INTO t_duty (duty_id, merchant_id, duty_name, status, description, duty_type)
VALUES (1, 1, '超级管理员', 'A', '演示环境内置超级管理员', 'SYSTEM');

INSERT INTO t_account (acct_id, account_key, account_name, password, account_status, is_active,
                       create_date, modify_date, salt, role_ids, locked, owner_id,
                       real_name, merchant_id, store_id, staff_id)
VALUES (1, 'demo-key-0000000001', 'bahar', 'b380f7a1afe140f323a3528a0fd709c65e65e2a1',
        1, 1, NOW(), NOW(), '1a2b3c4d5e6f7a8b', '1', 0, 1, '演示管理员', 1, 1, 0);

INSERT INTO t_account_duty (acc_duty_id, acct_id, duty_id) VALUES (1, 1, 1);

-- ############################################################
-- 4) bahar-health  （康养美业 baharHealth）
-- ############################################################
USE `bahar-health`;

DELETE FROM t_account_duty WHERE acc_duty_id = 1;
DELETE FROM t_account WHERE acct_id = 1;
DELETE FROM t_duty WHERE duty_id = 1;
DELETE FROM mt_store WHERE ID = 1;
DELETE FROM mt_merchant WHERE ID = 1;
DELETE FROM t_platform WHERE owner_id = 1;

INSERT INTO t_platform (owner_id, name, status, description, platform_type)
VALUES (1, 'bahar演示平台', 1, '演示环境平台方', 1);

INSERT INTO mt_merchant (ID, TYPE, NO, NAME, CONTACT, PHONE, ADDRESS, DESCRIPTION,
                         CREATE_TIME, UPDATE_TIME, START_TIME, END_TIME, STATUS, OPERATOR)
VALUES (1, 'MERCHANT', '10001', '演示康养门店', '演示联系人', '13800138000', '演示地址',
        'baharHealth 演示环境商户', NOW(), NOW(), '2020-01-01 00:00:00', '2030-12-31 23:59:59', 'A', 'system');

INSERT INTO mt_store (ID, MERCHANT_ID, NAME, IS_DEFAULT, CONTACT, PHONE, ADDRESS,
                      CREATE_TIME, UPDATE_TIME, STATUS, OPERATOR)
VALUES (1, 1, '演示康养总店', 'Y', '演示联系人', '13800138000', '演示地址', NOW(), NOW(), 'A', 'system');

INSERT INTO t_duty (duty_id, merchant_id, duty_name, status, description, duty_type)
VALUES (1, 1, '超级管理员', 'A', '演示环境内置超级管理员', 'SYSTEM');

INSERT INTO t_account (acct_id, account_key, account_name, password, account_status, is_active,
                       create_date, modify_date, salt, role_ids, locked, owner_id,
                       real_name, merchant_id, store_id, staff_id)
VALUES (1, 'demo-key-0000000001', 'bahar', 'b380f7a1afe140f323a3528a0fd709c65e65e2a1',
        1, 1, NOW(), NOW(), '1a2b3c4d5e6f7a8b', '1', 0, 1, '演示管理员', 1, 1, 0);

INSERT INTO t_account_duty (acc_duty_id, acct_id, duty_id) VALUES (1, 1, 1);

-- ============================================================
-- 执行完成
-- ============================================================
SELECT 'bahar-db' AS db_name, (SELECT COUNT(*) FROM `bahar-db`.t_account) AS account_rows,
       (SELECT COUNT(*) FROM `bahar-db`.mt_merchant) AS merchant_rows
UNION ALL SELECT 'bahar-car', (SELECT COUNT(*) FROM `bahar-car`.t_account), (SELECT COUNT(*) FROM `bahar-car`.mt_merchant)
UNION ALL SELECT 'bahar-catering', (SELECT COUNT(*) FROM `bahar-catering`.t_account), (SELECT COUNT(*) FROM `bahar-catering`.mt_merchant)
UNION ALL SELECT 'bahar-health', (SELECT COUNT(*) FROM `bahar-health`.t_account), (SELECT COUNT(*) FROM `bahar-health`.mt_merchant);
