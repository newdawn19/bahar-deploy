-- 修 8083（餐饮）轮播图菜单报 Unknown column 'position'
--
-- 根因：baharCatering 工程的 MtBanner 实体带 position 字段（展示位置，
-- 对应 PositionEnum：m_home_banner / m_home_ads），但建库脚本里的
-- mt_banner 表没有这一列，SELECT 时直接 SQLSyntaxErrorException。
-- 其余三套代码没有该字段，所以只有餐饮库报错。
--
-- 处理：四库统一补列（保持结构一致，任意一套代码切库都能跑），
-- 并按 sort 回填：前 3 条=首页焦点图，其余=首页广告位。
-- 幂等：列已存在时 ADD COLUMN 会报错，属于预期，可忽略。

ALTER TABLE mt_banner ADD COLUMN position varchar(32) DEFAULT NULL COMMENT '展示位置' AFTER title;

UPDATE mt_banner
SET position = 'm_home_banner'
WHERE position IS NULL
  AND ID IN (SELECT ID FROM (SELECT ID FROM mt_banner ORDER BY sort LIMIT 3) t);

UPDATE mt_banner SET position = 'm_home_ads' WHERE position IS NULL;
