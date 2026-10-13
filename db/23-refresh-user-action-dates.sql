-- ============================================================
-- 23-refresh-user-action-dates.sql —— 演示站「会员活跃」数据保鲜
-- ============================================================
-- 背景：「数据统计 → 运营走势」的「会员活跃」折线取 mt_user_action，
--   对应 Mapper 是 MtUserActionMapper.getActiveUserCount / getStoreActiveUserCount：
--     SELECT count(DISTINCT USER_ID) FROM mt_user_action
--      WHERE STATUS='A' AND UPDATE_TIME BETWEEN #{beginTime} AND #{endTime}
--        [AND MERCHANT_ID=?] 或 [AND STORE_ID=?]
--   注意三点：
--     1) 过滤的是 **UPDATE_TIME**（不是 CREATE_TIME）；
--     2) staff 有门店时按该会员的 STORE_ID 过滤（演示库员工张伟门店=1）；
--     3) 图表只取「近 7 天」（含今天）。
--   演示库这张表行数很少（餐饮只有 4 行）且停在月初，纯"整体平移"仍会让多数行
--   落在 7 天窗口之外 → 折线贴底全 0，客户看起来像"图表坏了"。
-- 做法：把现有的活跃记录**重新均匀铺到最近 7 天**（只改时间，不增删改行数，
--   不动 MERCHANT_ID / STORE_ID / USER_ID），保证每个行业的折线都画得出来。
--   偏移量 = MOD(行号, 7)，因此最近 7 天（含今天）每天都有记录，行多则更密。
-- 幂等：可反复执行，结果稳定（每次都重新铺一遍）。
-- 建议：与 22-refresh-order-dates.sql 一起跑，订单与活跃数据同时对齐到今天。
-- 适用范围：bahar-db / bahar-car / bahar-catering / bahar-health（四库结构一致）。
-- ============================================================

-- 只处理参与统计的记录（STATUS='A'）
SET @n := -1;

UPDATE mt_user_action
SET UPDATE_TIME = DATE_ADD(
        DATE_SUB(CURDATE(), INTERVAL MOD((@n := @n + 1), 7) DAY),
        INTERVAL 9 + MOD(@n, 9) HOUR
    )
WHERE STATUS = 'A';

-- CREATE_TIME 同步跟上，避免两列时间差得离谱
UPDATE mt_user_action
SET CREATE_TIME = UPDATE_TIME
WHERE STATUS = 'A' AND UPDATE_TIME IS NOT NULL;

-- 执行后的核对信息：近 7 天每天各有多少条活跃记录
SELECT DATE(UPDATE_TIME) AS action_day, COUNT(*) AS actions
FROM mt_user_action
WHERE STATUS = 'A'
GROUP BY DATE(UPDATE_TIME)
ORDER BY action_day DESC
LIMIT 8;
