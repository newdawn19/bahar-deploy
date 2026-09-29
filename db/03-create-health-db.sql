-- ============================================================
-- bahar-health 康养美业 —— 从主库复制表结构（幂等）
-- 生成时间: 2026-09-27
-- 说明: 康养工程 64 个 @TableName 实体表与主库同名且结构一致，
--       全部采用 CREATE TABLE ... LIKE 复制（含索引与自增主键）
-- ============================================================

CREATE DATABASE IF NOT EXISTS `bahar-health` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE `bahar-health`;

CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_address` LIKE `bahar-db`.`mt_address`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_article` LIKE `bahar-db`.`mt_article`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_balance` LIKE `bahar-db`.`mt_balance`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_banner` LIKE `bahar-db`.`mt_banner`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_book` LIKE `bahar-db`.`mt_book`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_book_cate` LIKE `bahar-db`.`mt_book_cate`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_book_item` LIKE `bahar-db`.`mt_book_item`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_cart` LIKE `bahar-db`.`mt_cart`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_commission_cash` LIKE `bahar-db`.`mt_commission_cash`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_commission_log` LIKE `bahar-db`.`mt_commission_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_commission_relation` LIKE `bahar-db`.`mt_commission_relation`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_commission_rule` LIKE `bahar-db`.`mt_commission_rule`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_commission_rule_item` LIKE `bahar-db`.`mt_commission_rule_item`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_confirm_log` LIKE `bahar-db`.`mt_confirm_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_coupon` LIKE `bahar-db`.`mt_coupon`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_coupon_goods` LIKE `bahar-db`.`mt_coupon_goods`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_coupon_group` LIKE `bahar-db`.`mt_coupon_group`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_give` LIKE `bahar-db`.`mt_give`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_give_item` LIKE `bahar-db`.`mt_give_item`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_goods` LIKE `bahar-db`.`mt_goods`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_goods_cate` LIKE `bahar-db`.`mt_goods_cate`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_goods_sku` LIKE `bahar-db`.`mt_goods_sku`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_goods_spec` LIKE `bahar-db`.`mt_goods_spec`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_invoice` LIKE `bahar-db`.`mt_invoice`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_merchant` LIKE `bahar-db`.`mt_merchant`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_message` LIKE `bahar-db`.`mt_message`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_open_gift` LIKE `bahar-db`.`mt_open_gift`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_open_gift_item` LIKE `bahar-db`.`mt_open_gift_item`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_order` LIKE `bahar-db`.`mt_order`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_order_address` LIKE `bahar-db`.`mt_order_address`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_order_goods` LIKE `bahar-db`.`mt_order_goods`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_point` LIKE `bahar-db`.`mt_point`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_printer` LIKE `bahar-db`.`mt_printer`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_refund` LIKE `bahar-db`.`mt_refund`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_region` LIKE `bahar-db`.`mt_region`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_send_log` LIKE `bahar-db`.`mt_send_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_setting` LIKE `bahar-db`.`mt_setting`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_settlement` LIKE `bahar-db`.`mt_settlement`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_settlement_order` LIKE `bahar-db`.`mt_settlement_order`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_sms_sended_log` LIKE `bahar-db`.`mt_sms_sended_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_sms_template` LIKE `bahar-db`.`mt_sms_template`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_staff` LIKE `bahar-db`.`mt_staff`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_stock` LIKE `bahar-db`.`mt_stock`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_stock_item` LIKE `bahar-db`.`mt_stock_item`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_store` LIKE `bahar-db`.`mt_store`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_store_goods` LIKE `bahar-db`.`mt_store_goods`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_upload_shipping_log` LIKE `bahar-db`.`mt_upload_shipping_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user` LIKE `bahar-db`.`mt_user`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_action` LIKE `bahar-db`.`mt_user_action`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_coupon` LIKE `bahar-db`.`mt_user_coupon`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_grade` LIKE `bahar-db`.`mt_user_grade`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_group` LIKE `bahar-db`.`mt_user_group`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_tag` LIKE `bahar-db`.`mt_user_tag`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_tag_relation` LIKE `bahar-db`.`mt_user_tag_relation`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_user_tag_rule` LIKE `bahar-db`.`mt_user_tag_rule`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`mt_verify_code` LIKE `bahar-db`.`mt_verify_code`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_account` LIKE `bahar-db`.`t_account`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_account_duty` LIKE `bahar-db`.`t_account_duty`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_action_log` LIKE `bahar-db`.`t_action_log`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_duty` LIKE `bahar-db`.`t_duty`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_duty_source` LIKE `bahar-db`.`t_duty_source`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_gen_code` LIKE `bahar-db`.`t_gen_code`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_platform` LIKE `bahar-db`.`t_platform`;
CREATE TABLE IF NOT EXISTS `bahar-health`.`t_source` LIKE `bahar-db`.`t_source`;

SELECT 'bahar-health' AS '库', COUNT(*) AS '表数', 64 AS '目标' FROM information_schema.tables WHERE table_schema='bahar-health';
