-- ============================================================
-- bahar 演示环境 —— 补齐缺失表结构（幂等，可重复执行）
-- 生成时间: 2026-09-27
--
-- 全部使用 CREATE TABLE IF NOT EXISTS，已存在的表自动跳过
-- 只建表，不删、不改任何已有对象；已存在的业务数据不受影响
--
-- 补齐来源:
--   A. 从主库同名表结构复制 (CREATE TABLE ... LIKE)
--   B. 取自 baharCatering/db/bahar-db-entities-sync.sql 的实体定义
--   C. 从 Java 实体类字段反推生成
-- ============================================================


-- ############################################################
-- 1) bahar-db  （主系统 bahar）补 4 张
-- ############################################################
-- [C] mt_stock_check / mt_stock_check_item / mt_user_balance —— 实体反推
CREATE TABLE IF NOT EXISTS `bahar-db`.`mt_stock_check` (
  `ID` INT NOT NULL AUTO_INCREMENT COMMENT '',
  `MERCHANT_ID` INT NULL,
  `STORE_ID` INT NULL,
  `CHECK_NO` VARCHAR(255) NULL,
  `CHECK_TIME` DATETIME NULL,
  `DESCRIPTION` VARCHAR(255) NULL,
  `CREATE_TIME` DATETIME NULL,
  `UPDATE_TIME` DATETIME NULL,
  `OPERATOR` VARCHAR(255) NULL,
  `STATUS` VARCHAR(255) NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

CREATE TABLE IF NOT EXISTS `bahar-db`.`mt_stock_check_item` (
  `ID` INT NOT NULL AUTO_INCREMENT COMMENT '',
  `CHECK_ID` INT NULL,
  `GOODS_ID` INT NULL,
  `SKU_ID` INT NULL,
  `SYSTEM_STOCK` DECIMAL(12,2) NULL,
  `ACTUAL_STOCK` DECIMAL(12,2) NULL,
  `DIFF_STOCK` DECIMAL(12,2) NULL,
  `DESCRIPTION` VARCHAR(255) NULL,
  `CREATE_TIME` DATETIME NULL,
  `UPDATE_TIME` DATETIME NULL,
  `STATUS` VARCHAR(255) NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

CREATE TABLE IF NOT EXISTS `bahar-db`.`mt_user_balance` (
  `ID` INT NOT NULL AUTO_INCREMENT COMMENT '',
  `USER_ID` INT NULL,
  `AMOUNT` DECIMAL(12,2) NULL,
  `CREATE_TIME` DATETIME NULL,
  `EXPIRED` DATETIME NULL,
  `MERCHANT_ID` INT NULL,
  `STORE_ID` INT NULL,
  `OPERATOR` VARCHAR(255) NULL,
  `ORDER_ID` INT NULL,
  `REMARK` VARCHAR(255) NULL,
  `STATUS` VARCHAR(255) NULL,
  `UPDATE_TIME` DATETIME NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

-- [B] mt_invoice —— 取自 entities-sync
  CREATE TABLE IF NOT EXISTS `bahar-db`.`mt_invoice` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `merchant_id` INT NULL,
  `store_id` INT NULL,
  `user_id` INT NULL,
  `order_id` INT NULL,
  `order_sn` VARCHAR(255) NULL,
  `invoice_time` DATETIME NULL,
  `invoice_amount` DECIMAL(12,2) NULL,
  `title` VARCHAR(255) NULL,
  `download_url` VARCHAR(255) NULL,
  `type` VARCHAR(255) NULL,
  `tax_code` VARCHAR(255) NULL,
  `bank_name` VARCHAR(255) NULL,
  `bank_card_no` VARCHAR(255) NULL,
  `bank_card_name` VARCHAR(255) NULL,
  `description` VARCHAR(255) NULL,
  `email` VARCHAR(255) NULL,
  `mobile` VARCHAR(255) NULL,
  `create_time` DATETIME NULL,
  `update_time` DATETIME NULL,
  `operator` VARCHAR(255) NULL,
  `status` VARCHAR(255) NULL,
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';


-- ############################################################
-- 2) bahar-car  （汽车 baharCar）补 8 张
-- ############################################################
-- [A] 5 张直接从主库复制结构（含索引）
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_book_cate` LIKE `bahar-db`.`mt_book_cate`;
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_printer` LIKE `bahar-db`.`mt_printer`;
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_user_tag` LIKE `bahar-db`.`mt_user_tag`;
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_user_tag_relation` LIKE `bahar-db`.`mt_user_tag_relation`;
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_user_tag_rule` LIKE `bahar-db`.`mt_user_tag_rule`;

-- [B] mt_invoice —— 取自 entities-sync
  CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_invoice` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `merchant_id` INT NULL,
  `store_id` INT NULL,
  `user_id` INT NULL,
  `order_id` INT NULL,
  `order_sn` VARCHAR(255) NULL,
  `invoice_time` DATETIME NULL,
  `invoice_amount` DECIMAL(12,2) NULL,
  `title` VARCHAR(255) NULL,
  `download_url` VARCHAR(255) NULL,
  `type` VARCHAR(255) NULL,
  `tax_code` VARCHAR(255) NULL,
  `bank_name` VARCHAR(255) NULL,
  `bank_card_no` VARCHAR(255) NULL,
  `bank_card_name` VARCHAR(255) NULL,
  `description` VARCHAR(255) NULL,
  `email` VARCHAR(255) NULL,
  `mobile` VARCHAR(255) NULL,
  `create_time` DATETIME NULL,
  `update_time` DATETIME NULL,
  `operator` VARCHAR(255) NULL,
  `status` VARCHAR(255) NULL,
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

-- [C] mt_vehicle / mt_vehicle_order —— 汽车行业核心表，实体反推
CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_vehicle` (
  `ID` INT NOT NULL AUTO_INCREMENT COMMENT '',
  `USER_ID` INT NULL,
  `MERCHANT_ID` INT NULL,
  `VEHICLE_MODEL` VARCHAR(255) NULL,
  `VEHICLE_TYPE` VARCHAR(255) NULL,
  `VEHICLE_PLATE_NO` VARCHAR(255) NULL,
  `VEHICLE_COLOR` VARCHAR(255) NULL,
  `VEHICLE_BRAND` VARCHAR(255) NULL,
  `VIN` VARCHAR(255) NULL,
  `STATUS` VARCHAR(255) NULL,
  `IS_DEFAULT` VARCHAR(255) NULL,
  `OPERATOR` VARCHAR(255) NULL,
  `CREATE_TIME` DATETIME NULL,
  `UPDATE_TIME` DATETIME NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

CREATE TABLE IF NOT EXISTS `bahar-car`.`mt_vehicle_order` (
  `ID` INT NOT NULL AUTO_INCREMENT COMMENT '',
  `USER_ID` INT NULL,
  `MERCHANT_ID` INT NULL,
  `STORE_ID` INT NULL,
  `ORDER_SN` VARCHAR(255) NULL,
  `VEHICLE_PLATE_NO` VARCHAR(255) NULL,
  `COUPON_ID` INT NULL,
  `STATUS` VARCHAR(255) NULL,
  `SCAN_CODE` VARCHAR(255) NULL,
  `REMARK` VARCHAR(255) NULL,
  `OPERATOR` VARCHAR(255) NULL,
  `CREATE_TIME` DATETIME NULL,
  `UPDATE_TIME` DATETIME NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';


-- ############################################################
-- 3) bahar-catering  （餐饮 baharCatering）补 8 张
-- ############################################################
-- [A] 5 张直接从主库复制结构（含索引）
CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_book_cate` LIKE `bahar-db`.`mt_book_cate`;
CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_printer` LIKE `bahar-db`.`mt_printer`;
CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_user_tag` LIKE `bahar-db`.`mt_user_tag`;
CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_user_tag_relation` LIKE `bahar-db`.`mt_user_tag_relation`;
CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_user_tag_rule` LIKE `bahar-db`.`mt_user_tag_rule`;

-- [B] mt_invoice / mt_rider / mt_rider_order —— 取自 entities-sync
  CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_invoice` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `merchant_id` INT NULL,
  `store_id` INT NULL,
  `user_id` INT NULL,
  `order_id` INT NULL,
  `order_sn` VARCHAR(255) NULL,
  `invoice_time` DATETIME NULL,
  `invoice_amount` DECIMAL(12,2) NULL,
  `title` VARCHAR(255) NULL,
  `download_url` VARCHAR(255) NULL,
  `type` VARCHAR(255) NULL,
  `tax_code` VARCHAR(255) NULL,
  `bank_name` VARCHAR(255) NULL,
  `bank_card_no` VARCHAR(255) NULL,
  `bank_card_name` VARCHAR(255) NULL,
  `description` VARCHAR(255) NULL,
  `email` VARCHAR(255) NULL,
  `mobile` VARCHAR(255) NULL,
  `create_time` DATETIME NULL,
  `update_time` DATETIME NULL,
  `operator` VARCHAR(255) NULL,
  `status` VARCHAR(255) NULL,
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

  CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_rider` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NULL,
  `rider_no` VARCHAR(255) NULL,
  `merchant_id` INT NULL,
  `store_id` INT NULL,
  `id_card` VARCHAR(255) NULL,
  `id_card_front` VARCHAR(255) NULL,
  `id_card_back` VARCHAR(255) NULL,
  `health_cert` VARCHAR(255) NULL,
  `status` VARCHAR(255) NULL,
  `description` VARCHAR(255) NULL,
  `create_time` DATETIME NULL,
  `update_time` DATETIME NULL,
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

  CREATE TABLE IF NOT EXISTS `bahar-catering`.`mt_rider_order` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NULL,
  `rider_id` INT NULL,
  `merchant_id` INT NULL,
  `store_id` INT NULL,
  `status` VARCHAR(255) NULL,
  `accept_time` DATETIME NULL,
  `pickup_time` DATETIME NULL,
  `deliver_time` DATETIME NULL,
  `complete_time` DATETIME NULL,
  `delivery_fee` DECIMAL(12,2) NULL,
  `remark` VARCHAR(255) NULL,
  `create_time` DATETIME NULL,
  `update_time` DATETIME NULL,
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='generated from entity';

-- ============================================================
-- 校验：三个库的表数应分别为 67 / 66 / 68
-- ============================================================
SELECT 'bahar-db' AS '库', COUNT(*) AS '现有表数', 67 AS '目标' FROM information_schema.tables WHERE table_schema='bahar-db'
UNION ALL SELECT 'bahar-car', COUNT(*), 66 FROM information_schema.tables WHERE table_schema='bahar-car'
UNION ALL SELECT 'bahar-catering', COUNT(*), 68 FROM information_schema.tables WHERE table_schema='bahar-catering';
