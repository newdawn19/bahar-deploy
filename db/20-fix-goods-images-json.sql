-- 修复演示数据 mt_goods.IMAGES 的存储格式：逗号分隔 -> JSON 数组字符串
--
-- 背景：应用对 mt_goods.IMAGES 的约定是「JSON 数组字符串」，例如
--   ["/static/uploadFiles/goods/1001.jpg","/static/uploadFiles/goods/1001_1.jpg"]
-- 写入侧证据：
--   GoodsServiceImpl.java:955   JSONObject.toJSONString(images.split(","))
--   MerchantGoodsController:201 mtGoods.setImages(JSONObject.toJSONString(relativeImages))
-- 读取侧证据：
--   BackendGoodsController:181  JSONArray.parseArray(goods.getImages(), String.class)
--   MerchantGoodsController:121 JSONArray.parseArray(goods.getImages(), String.class)
--   ClientGoodsController:182   objectMapper.readValue(getImages(), List)
--
-- 而演示数据（deploy/db/13-gen-images.py 生成）直接灌成了逗号分隔：
--   /static/uploadFiles/goods/1001.jpg,/static/uploadFiles/goods/1001_1.jpg
-- 导致所有 JSON 解析失败 -> 客户端「商品详情」接口 images 恒为空 -> 详情页轮播图空白。
-- （生成器已在同批次修好，本脚本用于修正已经写坏的现存数据。）
--
-- 本脚本把逗号分隔的行转成 JSON 数组。幂等：只处理非空且不以 '[' 开头的行。
-- 用法（对四个库各执行一次）：
--   mysql -uroot -pXXX bahar-db        < 20-fix-goods-images-json.sql
--   mysql -uroot -pXXX bahar-car       < 20-fix-goods-images-json.sql
--   mysql -uroot -pXXX bahar-catering  < 20-fix-goods-images-json.sql
--   mysql -uroot -pXXX bahar-health    < 20-fix-goods-images-json.sql

UPDATE mt_goods
SET IMAGES = CONCAT('["', REPLACE(IMAGES, ',', '","'), '"]')
WHERE IMAGES IS NOT NULL
  AND IMAGES <> ''
  AND IMAGES NOT LIKE '[%';
