-- 由 deploy/db/19-gen-home-diy.py 生成，勿手改
-- 会员端首页装修种子数据：四宫格导航 / 通栏广告图 / 前台可领券
-- 幂等：可反复执行；四库（零售 bahar-db、汽车 bahar-car、餐饮 bahar-catering、康养 bahar-health）内容一致

-- ===== retail（主色 #00acac）=====

-- 1) 四宫格导航：mt_setting NAME='navigation' AND TYPE='navigation'
DELETE FROM `bahar-db`.`mt_setting` WHERE `NAME`='navigation' AND `TYPE`='navigation' AND `MERCHANT_ID`=1;
INSERT INTO `bahar-db`.`mt_setting`
  (`MERCHANT_ID`,`STORE_ID`,`TYPE`,`NAME`,`VALUE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,'navigation','navigation','[{"name":"买单支付","tips":"支付攒积分","url":"pages/pay/index","icon":"/static/uploadFiles/nav/nav-1.png","sort":4,"status":"A"},{"name":"领券中心","tips":"领券更优惠","url":"subPages/coupon/list","icon":"/static/uploadFiles/nav/nav-2.png","sort":3,"status":"A"},{"name":"积分兑换","tips":"纯积分换好礼","url":"pages/points/detail","icon":"/static/uploadFiles/nav/nav-3.png","sort":2,"status":"A"},{"name":"邀请有礼","tips":"好礼相送","url":"pages/share/index","icon":"/static/uploadFiles/nav/nav-4.png","sort":1,"status":"A"}]','会员端首页四宫格导航','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- 2) 通栏广告图：mt_banner 一条 STORE_ID=0（对所有门店可见），图片在 uploadFiles/ads/ 下
DELETE FROM `bahar-db`.`mt_banner` WHERE `ID`=201;
INSERT INTO `bahar-db`.`mt_banner`
  (`ID`,`TITLE`,`position`,`MERCHANT_ID`,`STORE_ID`,`URL`,`IMAGE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`SORT`,`STATUS`)
VALUES (201,'会员日狂欢','m_home_ads',1,0,'subPages/coupon/list','/static/uploadFiles/ads/home-ad-1.jpg','首页通栏广告图','2026-10-11 10:00:00','2026-10-11 10:00:00','demo',1,'A');

-- 3) 优惠券：开放前台领取（coupon/list 默认只返回 SEND_WAY='front'）
UPDATE `bahar-db`.`mt_coupon` SET `SEND_WAY`='front', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `TYPE`='C' AND `MERCHANT_ID`=1;

-- 4) 券面文案：门槛（sellingPoint 由 OUT_RULE 推算）+ 适用范围（会员端取 description）
UPDATE `bahar-db`.`mt_coupon` SET `OUT_RULE`='100', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID`=102 AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-db`.`mt_coupon` SET `DESCRIPTION`='全场通用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (1,101,104) AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-db`.`mt_coupon` SET `DESCRIPTION`='指定商品可用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (2,102,103) AND `TYPE`='C' AND `MERCHANT_ID`=1;

-- 5) 补建卡券分组：mt_coupon.GROUP_ID 指向 1/2，但库里只有 3/201/202，
--    UserCouponServiceImpl#receiveCoupon 会 new 出 null 分组 -> NullPointerException，
--    领券接口直接 500。补上这两条分组，领券才真能入账。
DELETE FROM `bahar-db`.`mt_coupon_group` WHERE `ID` IN (1,2);
INSERT INTO `bahar-db`.`mt_coupon_group`
  (`ID`,`MERCHANT_ID`,`STORE_ID`,`NAME`,`MONEY`,`NUM`,`TOTAL`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,1,'新客与活动券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A'),
       (2,1,1,'新客与活动券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- ===== car（主色 #373f64）=====

-- 1) 四宫格导航：mt_setting NAME='navigation' AND TYPE='navigation'
DELETE FROM `bahar-car`.`mt_setting` WHERE `NAME`='navigation' AND `TYPE`='navigation' AND `MERCHANT_ID`=1;
INSERT INTO `bahar-car`.`mt_setting`
  (`MERCHANT_ID`,`STORE_ID`,`TYPE`,`NAME`,`VALUE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,'navigation','navigation','[{"name":"买单支付","tips":"支付攒积分","url":"pages/pay/index","icon":"/static/uploadFiles/nav/nav-1.png","sort":4,"status":"A"},{"name":"领券中心","tips":"领券更优惠","url":"subPages/coupon/list","icon":"/static/uploadFiles/nav/nav-2.png","sort":3,"status":"A"},{"name":"积分兑换","tips":"纯积分换好礼","url":"pages/points/detail","icon":"/static/uploadFiles/nav/nav-3.png","sort":2,"status":"A"},{"name":"邀请有礼","tips":"好礼相送","url":"pages/share/index","icon":"/static/uploadFiles/nav/nav-4.png","sort":1,"status":"A"}]','会员端首页四宫格导航','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- 2) 通栏广告图：mt_banner 一条 STORE_ID=0（对所有门店可见），图片在 uploadFiles/ads/ 下
DELETE FROM `bahar-car`.`mt_banner` WHERE `ID`=201;
INSERT INTO `bahar-car`.`mt_banner`
  (`ID`,`TITLE`,`position`,`MERCHANT_ID`,`STORE_ID`,`URL`,`IMAGE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`SORT`,`STATUS`)
VALUES (201,'会员日狂欢','m_home_ads',1,0,'subPages/coupon/list','/static/uploadFiles/ads/home-ad-1.jpg','首页通栏广告图','2026-10-11 10:00:00','2026-10-11 10:00:00','demo',1,'A');

-- 3) 优惠券：开放前台领取（coupon/list 默认只返回 SEND_WAY='front'）
UPDATE `bahar-car`.`mt_coupon` SET `SEND_WAY`='front', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `TYPE`='C' AND `MERCHANT_ID`=1;

-- 4) 券面文案：门槛（sellingPoint 由 OUT_RULE 推算）+ 适用范围（会员端取 description）
UPDATE `bahar-car`.`mt_coupon` SET `OUT_RULE`='100', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID`=102 AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-car`.`mt_coupon` SET `DESCRIPTION`='全场通用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (1,101,104) AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-car`.`mt_coupon` SET `DESCRIPTION`='指定商品可用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (2,102,103) AND `TYPE`='C' AND `MERCHANT_ID`=1;

-- 5) 补建卡券分组：mt_coupon.GROUP_ID 指向 1/2，但库里只有 3/201/202，
--    UserCouponServiceImpl#receiveCoupon 会 new 出 null 分组 -> NullPointerException，
--    领券接口直接 500。补上这两条分组，领券才真能入账。
DELETE FROM `bahar-car`.`mt_coupon_group` WHERE `ID` IN (1,2);
INSERT INTO `bahar-car`.`mt_coupon_group`
  (`ID`,`MERCHANT_ID`,`STORE_ID`,`NAME`,`MONEY`,`NUM`,`TOTAL`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,1,'洗车优惠券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A'),
       (2,1,1,'洗车优惠券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- ===== food（主色 #113a28）=====

-- 1) 四宫格导航：mt_setting NAME='navigation' AND TYPE='navigation'
DELETE FROM `bahar-catering`.`mt_setting` WHERE `NAME`='navigation' AND `TYPE`='navigation' AND `MERCHANT_ID`=1;
INSERT INTO `bahar-catering`.`mt_setting`
  (`MERCHANT_ID`,`STORE_ID`,`TYPE`,`NAME`,`VALUE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,'navigation','navigation','[{"name":"买单支付","tips":"支付攒积分","url":"pages/pay/index","icon":"/static/uploadFiles/nav/nav-1.png","sort":4,"status":"A"},{"name":"领券中心","tips":"领券更优惠","url":"subPages/coupon/list","icon":"/static/uploadFiles/nav/nav-2.png","sort":3,"status":"A"},{"name":"积分兑换","tips":"纯积分换好礼","url":"pages/points/detail","icon":"/static/uploadFiles/nav/nav-3.png","sort":2,"status":"A"},{"name":"邀请有礼","tips":"好礼相送","url":"pages/share/index","icon":"/static/uploadFiles/nav/nav-4.png","sort":1,"status":"A"}]','会员端首页四宫格导航','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- 2) 通栏广告图：mt_banner 一条 STORE_ID=0（对所有门店可见），图片在 uploadFiles/ads/ 下
DELETE FROM `bahar-catering`.`mt_banner` WHERE `ID`=201;
INSERT INTO `bahar-catering`.`mt_banner`
  (`ID`,`TITLE`,`position`,`MERCHANT_ID`,`STORE_ID`,`URL`,`IMAGE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`SORT`,`STATUS`)
VALUES (201,'会员日狂欢','m_home_ads',1,0,'subPages/coupon/list','/static/uploadFiles/ads/home-ad-1.jpg','首页通栏广告图','2026-10-11 10:00:00','2026-10-11 10:00:00','demo',1,'A');

-- 3) 优惠券：开放前台领取（coupon/list 默认只返回 SEND_WAY='front'）
UPDATE `bahar-catering`.`mt_coupon` SET `SEND_WAY`='front', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `TYPE`='C' AND `MERCHANT_ID`=1;

-- 4) 券面文案：门槛（sellingPoint 由 OUT_RULE 推算）+ 适用范围（会员端取 description）
UPDATE `bahar-catering`.`mt_coupon` SET `OUT_RULE`='100', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID`=102 AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-catering`.`mt_coupon` SET `DESCRIPTION`='全场通用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (1,101,104) AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-catering`.`mt_coupon` SET `DESCRIPTION`='指定商品可用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (2,102,103) AND `TYPE`='C' AND `MERCHANT_ID`=1;

-- 5) 补建卡券分组：mt_coupon.GROUP_ID 指向 1/2，但库里只有 3/201/202，
--    UserCouponServiceImpl#receiveCoupon 会 new 出 null 分组 -> NullPointerException，
--    领券接口直接 500。补上这两条分组，领券才真能入账。
DELETE FROM `bahar-catering`.`mt_coupon_group` WHERE `ID` IN (1,2);
INSERT INTO `bahar-catering`.`mt_coupon_group`
  (`ID`,`MERCHANT_ID`,`STORE_ID`,`NAME`,`MONEY`,`NUM`,`TOTAL`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,1,'到店优惠券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A'),
       (2,1,1,'到店优惠券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- ===== health（主色 #7c5cff）=====

-- 1) 四宫格导航：mt_setting NAME='navigation' AND TYPE='navigation'
DELETE FROM `bahar-health`.`mt_setting` WHERE `NAME`='navigation' AND `TYPE`='navigation' AND `MERCHANT_ID`=1;
INSERT INTO `bahar-health`.`mt_setting`
  (`MERCHANT_ID`,`STORE_ID`,`TYPE`,`NAME`,`VALUE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,'navigation','navigation','[{"name":"买单支付","tips":"支付攒积分","url":"pages/pay/index","icon":"/static/uploadFiles/nav/nav-1.png","sort":4,"status":"A"},{"name":"领券中心","tips":"领券更优惠","url":"subPages/coupon/list","icon":"/static/uploadFiles/nav/nav-2.png","sort":3,"status":"A"},{"name":"积分兑换","tips":"纯积分换好礼","url":"pages/points/detail","icon":"/static/uploadFiles/nav/nav-3.png","sort":2,"status":"A"},{"name":"邀请有礼","tips":"好礼相送","url":"pages/share/index","icon":"/static/uploadFiles/nav/nav-4.png","sort":1,"status":"A"}]','会员端首页四宫格导航','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

-- 2) 通栏广告图：mt_banner 一条 STORE_ID=0（对所有门店可见），图片在 uploadFiles/ads/ 下
DELETE FROM `bahar-health`.`mt_banner` WHERE `ID`=201;
INSERT INTO `bahar-health`.`mt_banner`
  (`ID`,`TITLE`,`position`,`MERCHANT_ID`,`STORE_ID`,`URL`,`IMAGE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`SORT`,`STATUS`)
VALUES (201,'会员日狂欢','m_home_ads',1,0,'subPages/coupon/list','/static/uploadFiles/ads/home-ad-1.jpg','首页通栏广告图','2026-10-11 10:00:00','2026-10-11 10:00:00','demo',1,'A');

-- 3) 优惠券：开放前台领取（coupon/list 默认只返回 SEND_WAY='front'）
UPDATE `bahar-health`.`mt_coupon` SET `SEND_WAY`='front', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `TYPE`='C' AND `MERCHANT_ID`=1;

-- 4) 券面文案：门槛（sellingPoint 由 OUT_RULE 推算）+ 适用范围（会员端取 description）
UPDATE `bahar-health`.`mt_coupon` SET `OUT_RULE`='100', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID`=102 AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-health`.`mt_coupon` SET `DESCRIPTION`='全场通用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (1,101,104) AND `TYPE`='C' AND `MERCHANT_ID`=1;
UPDATE `bahar-health`.`mt_coupon` SET `DESCRIPTION`='指定商品可用', `UPDATE_TIME`='2026-10-11 10:00:00' WHERE `ID` IN (2,102,103) AND `TYPE`='C' AND `MERCHANT_ID`=1;

-- 5) 补建卡券分组：mt_coupon.GROUP_ID 指向 1/2，但库里只有 3/201/202，
--    UserCouponServiceImpl#receiveCoupon 会 new 出 null 分组 -> NullPointerException，
--    领券接口直接 500。补上这两条分组，领券才真能入账。
DELETE FROM `bahar-health`.`mt_coupon_group` WHERE `ID` IN (1,2);
INSERT INTO `bahar-health`.`mt_coupon_group`
  (`ID`,`MERCHANT_ID`,`STORE_ID`,`NAME`,`MONEY`,`NUM`,`TOTAL`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)
VALUES (1,1,1,'康养体验券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A'),
       (2,1,1,'康养体验券',0.00,0,1000,'会员端前台可领取的卡券分组','2026-10-11 10:00:00','2026-10-11 10:00:00','demo','A');

