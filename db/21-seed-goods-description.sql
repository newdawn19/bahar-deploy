-- 给演示商品的「商品详情」(mt_goods.DESCRIPTION) 补齐富文本内容
--
-- 背景：演示数据只灌了名称/价格/库存，DESCRIPTION 全空。
--   客户端商品详情页在 description 为空时只渲染一句「亲，暂无商品描述」，
--   整页下半部分变成一大片空白，客户截图里看着像"没做完"。
-- 本脚本按商品名生成一段通用但完整的富文本说明（品牌/卖点/服务保障），
-- 让「商品详情」区域有内容。纯演示数据，幂等：只填空值行。
--
-- 用法（对四个库各执行一次）：
--   mysql -uroot -pXXX bahar-db        < 21-seed-goods-description.sql
--   mysql -uroot -pXXX bahar-car       < 21-seed-goods-description.sql
--   mysql -uroot -pXXX bahar-catering  < 21-seed-goods-description.sql
--   mysql -uroot -pXXX bahar-health    < 21-seed-goods-description.sql

UPDATE mt_goods
SET DESCRIPTION = CONCAT(
  '<p><strong>', NAME, '</strong></p>',
  '<p>精选优质货源，全程严选，品质可靠，是您值得信赖的选择。下单后门店极速备货，支持到店自提与配送。</p>',
  '<p><strong>服务保障</strong></p>',
  '<ul>',
    '<li>正规渠道 · 品质保障</li>',
    '<li>专业团队 · 严格把控</li>',
    '<li>售后无忧 · 专属客服在线</li>',
  '</ul>',
  '<p>温馨提示：页面内容仅供参考，具体以门店实际为准。</p>'
)
WHERE DESCRIPTION IS NULL OR DESCRIPTION = '';
