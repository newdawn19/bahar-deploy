-- ============================================================================
-- 24-add-name-en.sql
-- 目的：为 4 套业务库（零售/汽车/餐饮/康养）的 7 张核心表增加英文名称列，
--       供 C 端按语言返回商品/分类/券/等级/门店/轮播/文章名称。
-- 说明：MySQL 8.0 不支持 ALTER TABLE ADD COLUMN IF NOT EXISTS（该语法为 MariaDB
--       专有），故用存储过程 add_name_en_col 查询 INFORMATION_SCHEMA 判重后条件
--       执行 ALTER，保证脚本可重复（幂等）执行。字符集沿用 utf8mb4，不改建表
--       charset。
-- 执行：mysql --default-character-set=utf8mb4 -uroot -prootAdmin@0731 < 24-add-name-en.sql
-- ============================================================================

-- 选定一个默认库，避免存储过程内动态 ALTER 报 "No database selected"
-- （ALTER 仍使用 `库`.`表` 全限定名，不影响目标库）。
USE `mysql`;

DROP PROCEDURE IF EXISTS add_name_en_col;
DELIMITER $$
CREATE PROCEDURE add_name_en_col(
    IN p_db   VARCHAR(64),
    IN p_tbl  VARCHAR(64),
    IN p_col  VARCHAR(64),
    IN p_def  VARCHAR(512)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = p_db AND TABLE_NAME = p_tbl AND COLUMN_NAME = p_col
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_db, '`.`', p_tbl, '` ADD COLUMN `', p_col, '` ', p_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('ADDED  `', p_db, '`.`', p_tbl, '`.`', p_col, '`') AS action;
    ELSE
        SELECT CONCAT('EXISTS `', p_db, '`.`', p_tbl, '`.`', p_col, '` (skip)') AS action;
    END IF;
END$$
DELIMITER ;

-- ------------------------- 零售 bahar-db -------------------------
CALL add_name_en_col('bahar-db','mt_goods',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-db','mt_goods_cate', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-db','mt_coupon',     'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-db','mt_user_grade', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-db','mt_store',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-db','mt_banner',     'TITLE_EN', 'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');
CALL add_name_en_col('bahar-db','mt_article',    'TITLE_EN', 'varchar(200) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');

-- ------------------------- 汽车 bahar-car -------------------------
CALL add_name_en_col('bahar-car','mt_goods',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-car','mt_goods_cate', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-car','mt_coupon',     'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-car','mt_user_grade', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-car','mt_store',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-car','mt_banner',     'TITLE_EN', 'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');
CALL add_name_en_col('bahar-car','mt_article',    'TITLE_EN', 'varchar(200) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');

-- ------------------------- 餐饮 bahar-catering -------------------------
CALL add_name_en_col('bahar-catering','mt_goods',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-catering','mt_goods_cate', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-catering','mt_coupon',     'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-catering','mt_user_grade', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-catering','mt_store',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-catering','mt_banner',     'TITLE_EN', 'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');
CALL add_name_en_col('bahar-catering','mt_article',    'TITLE_EN', 'varchar(200) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');

-- ------------------------- 康养 bahar-health -------------------------
CALL add_name_en_col('bahar-health','mt_goods',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-health','mt_goods_cate', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-health','mt_coupon',     'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-health','mt_user_grade', 'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-health','mt_store',      'NAME_EN',  'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文名'' AFTER `NAME`');
CALL add_name_en_col('bahar-health','mt_banner',     'TITLE_EN', 'varchar(100) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');
CALL add_name_en_col('bahar-health','mt_article',    'TITLE_EN', 'varchar(200) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT ''英文标题'' AFTER `TITLE`');

DROP PROCEDURE IF EXISTS add_name_en_col;

SELECT '24-add-name-en.sql executed.' AS result;
