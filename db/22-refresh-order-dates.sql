-- ============================================================
-- 22-refresh-order-dates.sql —— 演示站「数据统计」数据保鲜
-- ============================================================
-- 背景：演示订单是 2026-09 的历史数据，而「数据统计」页默认看
--   今天 / 近3天 / 近7天 / 近15天 / 近30天，
--   结果今天与近七天全为 0、运营走势图空白、数据排行「暂无数据」。
-- 做法：把演示订单的时间整体平移到"最近"——
--   delta = DATEDIFF(CURDATE(), DATE(MAX(CREATE_TIME)))，
--   把 CREATE_TIME / UPDATE_TIME / PAY_TIME / CONFIRM_TIME 同时 +delta 天，
--   使最新订单正好落在"今天"，近七日柱状图即刻有数据。
-- 幂等：执行后 MAX(DATE(CREATE_TIME)) = CURDATE()，再次执行 delta=0 不改动；
--   隔天再执行会自动再次前移，保持"今天"持续有单（演示站长期保鲜）。
-- 注意：DATE_ADD(NULL, …) 结果为 NULL，故 PAY_TIME/CONFIRM_TIME 为空的行不受影响。
-- 适用范围：bahar-db / bahar-car / bahar-catering / bahar-health（四库结构一致）。
-- ============================================================

SET @delta := (SELECT IFNULL(DATEDIFF(CURDATE(), DATE(MAX(CREATE_TIME))), 0) FROM mt_order);

UPDATE mt_order
SET CREATE_TIME  = DATE_ADD(CREATE_TIME,  INTERVAL @delta DAY),
    UPDATE_TIME  = DATE_ADD(UPDATE_TIME,  INTERVAL @delta DAY),
    PAY_TIME     = DATE_ADD(PAY_TIME,     INTERVAL @delta DAY),
    CONFIRM_TIME = DATE_ADD(CONFIRM_TIME, INTERVAL @delta DAY)
WHERE @delta <> 0;

-- 执行后的核对信息：平移天数 + 现在的时间跨度
SELECT @delta AS delta_days,
       DATE(MIN(CREATE_TIME)) AS min_day,
       DATE(MAX(CREATE_TIME)) AS max_day,
       COUNT(*) AS orders,
       SUM(DATE(CREATE_TIME) = CURDATE()) AS today_orders
FROM mt_order;
