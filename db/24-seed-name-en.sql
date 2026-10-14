-- ============================================================================
-- 24-seed-name-en.sql
-- 目的：把演示种子数据的核心名称回填为英文（NAME_EN / TITLE_EN），
--       使 C 端可按语言返回商品/分类/券/等级/门店/轮播/文章名称。
-- 说明：按中文名精准匹配 UPDATE。演示数据中同名记录会批量更新，符合预期。
--       四个行业库各自独立执行；名字不存在的行业自动跳过（无匹配行）。
-- 依赖：需先执行 24-add-name-en.sql 建列。
-- 执行：mysql --default-character-set=utf8mb4 -uroot -prootAdmin@0731 < 24-seed-name-en.sql
-- ============================================================================

-- ============================ 零售 bahar-db ============================
USE `bahar-db`;

-- 分类
UPDATE `mt_goods_cate` SET `NAME_EN`='Snacks'        WHERE `NAME`='休闲零食';
UPDATE `mt_goods_cate` SET `NAME_EN`='Beverages'     WHERE `NAME`='酒水饮料';
UPDATE `mt_goods_cate` SET `NAME_EN`='Daily Goods'   WHERE `NAME`='日用百货';
UPDATE `mt_goods_cate` SET `NAME_EN`='Fresh Fruits'  WHERE `NAME`='生鲜水果';

-- 会员等级
UPDATE `mt_user_grade` SET `NAME_EN`='Regular'           WHERE `NAME`='普通会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Silver'            WHERE `NAME`='银卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Gold'              WHERE `NAME`='金卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Diamond'           WHERE `NAME`='钻石会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Monthly Card'      WHERE `NAME`='优选月卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Quarterly Card'    WHERE `NAME`='优选季卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Annual Card'       WHERE `NAME`='优选年卡';

-- 门店
UPDATE `mt_store` SET `NAME_EN`='Demo HQ Store'        WHERE `NAME`='演示总店';
UPDATE `mt_store` SET `NAME_EN`='East Store'           WHERE `NAME`='城东分店';
UPDATE `mt_store` SET `NAME_EN`='New District Flagship' WHERE `NAME`='新区旗舰店';

-- 券
UPDATE `mt_coupon` SET `NAME_EN`='¥5 off over ¥50 Coupon'        WHERE `NAME`='满50减5元优惠券';
UPDATE `mt_coupon` SET `NAME_EN`='¥10 No-threshold Coupon'       WHERE `NAME`='10元无门槛券';
UPDATE `mt_coupon` SET `NAME_EN`='¥100 Stored-value Card'        WHERE `NAME`='100元储值卡';
UPDATE `mt_coupon` SET `NAME_EN`='New Customer Exclusive Coupon' WHERE `NAME`='新客专享券';
UPDATE `mt_coupon` SET `NAME_EN`='¥20 off over ¥100 Coupon'      WHERE `NAME`='满100减20';
UPDATE `mt_coupon` SET `NAME_EN`='Member Day Coupon'             WHERE `NAME`='会员日券';
UPDATE `mt_coupon` SET `NAME_EN`='Holiday Gift Pack Coupon'      WHERE `NAME`='节日礼包券';

-- 轮播
UPDATE `mt_banner` SET `TITLE_EN`='Member Day 10% Off Storewide' WHERE `TITLE`='会员日全场9折';
UPDATE `mt_banner` SET `TITLE_EN`='New User Registration Coupon' WHERE `TITLE`='新客注册送券';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day 20% Off Storewide' WHERE `TITLE`='会员日全场8折';
UPDATE `mt_banner` SET `TITLE_EN`='Spring New Arrivals'          WHERE `TITLE`='春季新品上市';
UPDATE `mt_banner` SET `TITLE_EN`='Newcomer Exclusive Gift Pack' WHERE `TITLE`='新人专享礼包';
UPDATE `mt_banner` SET `TITLE_EN`='Store Environment Showcase'  WHERE `TITLE`='门店环境展示';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day Carnival'         WHERE `TITLE`='会员日狂欢';

-- 文章
UPDATE `mt_article` SET `TITLE_EN`='Member Day Carnival 20% Off'    WHERE `TITLE`='会员日狂欢 全场8折';
UPDATE `mt_article` SET `TITLE_EN`='Spring New Arrivals'            WHERE `TITLE`='春季新品上市';
UPDATE `mt_article` SET `TITLE_EN`='Store Relocation Notice'        WHERE `TITLE`='门店搬迁通知';
UPDATE `mt_article` SET `TITLE_EN`='Points Redemption Guide'        WHERE `TITLE`='积分兑换攻略';
UPDATE `mt_article` SET `TITLE_EN`='Holiday Business Hours'         WHERE `TITLE`='节假日营业时间';
UPDATE `mt_article` SET `TITLE_EN`='Summer Drink Festival'          WHERE `TITLE`='夏日饮品节';
UPDATE `mt_article` SET `TITLE_EN`='Member Exclusive Day'           WHERE `TITLE`='会员专享日';
UPDATE `mt_article` SET `TITLE_EN`='Year-end Points Reset Reminder' WHERE `TITLE`='积分年底清零提醒';

-- 商品
UPDATE `mt_goods` SET `NAME_EN`='Three Squirrels Daily Nuts'     WHERE `NAME`='三只松鼠每日坚果';
UPDATE `mt_goods` SET `NAME_EN`='Lay''s Chips Original 70g'      WHERE `NAME`='乐事薯片 原味70g';
UPDATE `mt_goods` SET `NAME_EN`='Yunnan Mengzi Pomegranate 2jin' WHERE `NAME`='云南蒙自石榴 2斤装';
UPDATE `mt_goods` SET `NAME_EN`='Yunnan Blueberry 125g'          WHERE `NAME`='云南蓝莓 125g';
UPDATE `mt_goods` SET `NAME_EN`='Membership Starter Package'     WHERE `NAME`='会员开卡套餐';
UPDATE `mt_goods` SET `NAME_EN`='Crest Toothpaste 120g'          WHERE `NAME`='佳洁士牙膏 120g';
UPDATE `mt_goods` SET `NAME_EN`='Genki Forest White Peach'       WHERE `NAME`='元气森林白桃味';
UPDATE `mt_goods` SET `NAME_EN`='Nongfu Spring 550ml'            WHERE `NAME`='农夫山泉 550ml';
UPDATE `mt_goods` SET `NAME_EN`='Nongfu Spring Drinking Water 550ml' WHERE `NAME`='农夫山泉饮用水 550ml';
UPDATE `mt_goods` SET `NAME_EN`='Weilong Spicy Snack'            WHERE `NAME`='卫龙亲嘴烧';
UPDATE `mt_goods` SET `NAME_EN`='Coca-Cola 330ml'                WHERE `NAME`='可口可乐 330ml';
UPDATE `mt_goods` SET `NAME_EN`='Paradise Folding Umbrella'      WHERE `NAME`='天堂三折雨伞';
UPDATE `mt_goods` SET `NAME_EN`='Oreo Sandwich Cookies'          WHERE `NAME`='奥利奥夹心饼干';
UPDATE `mt_goods` SET `NAME_EN`='Orion Choco Pie 12pcs'          WHERE `NAME`='好丽友派 12枚装';
UPDATE `mt_goods` SET `NAME_EN`='Ningxia Qilin Watermelon'       WHERE `NAME`='宁夏麒麟西瓜';
UPDATE `mt_goods` SET `NAME_EN`='Shandong Cherry 250g'           WHERE `NAME`='山东大樱桃 250g';
UPDATE `mt_goods` SET `NAME_EN`='Master Kong Iced Tea'           WHERE `NAME`='康师傅冰红茶';
UPDATE `mt_goods` SET `NAME_EN`='Xu Fu Ji Sachima'               WHERE `NAME`='徐福记沙琪玛';
UPDATE `mt_goods` SET `NAME_EN`='Hearttex Tissue 3-ply'          WHERE `NAME`='心相印抽纸 3层';
UPDATE `mt_goods` SET `NAME_EN`='Starbucks Latte 268ml'          WHERE `NAME`='星巴克拿铁 268ml';
UPDATE `mt_goods` SET `NAME_EN`='Thai Golden Pillow Durian'      WHERE `NAME`='泰国金枕榴莲';
UPDATE `mt_goods` SET `NAME_EN`='Qiaqia Hickory Sunflower Seeds' WHERE `NAME`='洽洽山核桃瓜子';
UPDATE `mt_goods` SET `NAME_EN`='Hainan Banana 1jin'             WHERE `NAME`='海南香蕉 1斤';
UPDATE `mt_goods` SET `NAME_EN`='Hainan Banana 500g'             WHERE `NAME`='海南香蕉 500g';
UPDATE `mt_goods` SET `NAME_EN`='Head & Shoulders Shampoo 500ml' WHERE `NAME`='海飞丝洗发水 500ml';
UPDATE `mt_goods` SET `NAME_EN`='Qingfeng Tissue 3-ply 24pk'     WHERE `NAME`='清风抽纸 3层24包';
UPDATE `mt_goods` SET `NAME_EN`='Wong Lo Kat Herbal Tea'         WHERE `NAME`='王老吉凉茶';
UPDATE `mt_goods` SET `NAME_EN`='Liby Laundry Detergent 1kg'     WHERE `NAME`='立白洗衣液 1kg';
UPDATE `mt_goods` SET `NAME_EN`='Red Fuji Apple 500g'            WHERE `NAME`='红富士苹果 500g';
UPDATE `mt_goods` SET `NAME_EN`='Safeguard Body Wash 720ml'      WHERE `NAME`='舒肤佳沐浴露 720ml';
UPDATE `mt_goods` SET `NAME_EN`='Bestore Pork Jerky'             WHERE `NAME`='良品铺子猪肉脯';
UPDATE `mt_goods` SET `NAME_EN`='Supor Thermos 500ml'            WHERE `NAME`='苏泊尔保温杯 500ml';
UPDATE `mt_goods` SET `NAME_EN`='Mengniu Milk 250ml'             WHERE `NAME`='蒙牛纯牛奶 250ml';
UPDATE `mt_goods` SET `NAME_EN`='Blue Moon Laundry Detergent 1kg' WHERE `NAME`='蓝月亮洗衣液 1kg';
UPDATE `mt_goods` SET `NAME_EN`='Gannan Navel Orange 1kg'        WHERE `NAME`='赣南脐橙 1kg';
UPDATE `mt_goods` SET `NAME_EN`='Jinhao Cotton Towel'            WHERE `NAME`='金号纯棉毛巾';
UPDATE `mt_goods` SET `NAME_EN`='Shine Muscat Grape 500g'        WHERE `NAME`='阳光玫瑰葡萄 500g';
UPDATE `mt_goods` SET `NAME_EN`='Tsingtao Beer 500ml'            WHERE `NAME`='青岛啤酒 500ml';
UPDATE `mt_goods` SET `NAME_EN`='Colgate Total Toothpaste'       WHERE `NAME`='高露洁全效牙膏';

-- ============================ 汽车 bahar-car ============================
USE `bahar-car`;

-- 分类
UPDATE `mt_goods_cate` SET `NAME_EN`='Car Wash Service'     WHERE `NAME`='洗车服务';
UPDATE `mt_goods_cate` SET `NAME_EN`='Beauty & Care'        WHERE `NAME`='美容养护';
UPDATE `mt_goods_cate` SET `NAME_EN`='Repair & Maintenance' WHERE `NAME`='维修保养';
UPDATE `mt_goods_cate` SET `NAME_EN`='Auto Accessories'     WHERE `NAME`='汽车用品';

-- 会员等级
UPDATE `mt_user_grade` SET `NAME_EN`='Regular'             WHERE `NAME`='普通会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Silver'              WHERE `NAME`='银卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Gold'                WHERE `NAME`='金卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Diamond'             WHERE `NAME`='钻石会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Car Wash Monthly Card' WHERE `NAME`='洗车月卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Care Quarterly Card' WHERE `NAME`='养护季卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Premium Annual Card' WHERE `NAME`='尊享年卡';

-- 门店
UPDATE `mt_store` SET `NAME_EN`='Demo Auto HQ Store'      WHERE `NAME`='演示汽车总店';
UPDATE `mt_store` SET `NAME_EN`='East Store'              WHERE `NAME`='城东分店';
UPDATE `mt_store` SET `NAME_EN`='New District Flagship'   WHERE `NAME`='新区旗舰店';

-- 券
UPDATE `mt_coupon` SET `NAME_EN`='50% off Car Wash Coupon'    WHERE `NAME`='洗车5折券';
UPDATE `mt_coupon` SET `NAME_EN`='¥50 off over ¥300 Coupon'   WHERE `NAME`='满300减50券';
UPDATE `mt_coupon` SET `NAME_EN`='¥1000 Top-up Card'         WHERE `NAME`='1000元充值卡';
UPDATE `mt_coupon` SET `NAME_EN`='New Customer Exclusive Coupon' WHERE `NAME`='新客专享券';
UPDATE `mt_coupon` SET `NAME_EN`='¥20 off over ¥100 Coupon'   WHERE `NAME`='满100减20';
UPDATE `mt_coupon` SET `NAME_EN`='Member Day Coupon'         WHERE `NAME`='会员日券';
UPDATE `mt_coupon` SET `NAME_EN`='Holiday Gift Pack Coupon'   WHERE `NAME`='节日礼包券';

-- 轮播
UPDATE `mt_banner` SET `TITLE_EN`='Spring Car Wash Festival' WHERE `TITLE`='春季洗车节';
UPDATE `mt_banner` SET `TITLE_EN`='Top-up Cashback'          WHERE `TITLE`='充值返现';
UPDATE `mt_banner` SET `TITLE_EN`='Member Car Wash 50% Off'  WHERE `TITLE`='会员洗车5折';
UPDATE `mt_banner` SET `TITLE_EN`='Premium Wash & Wax Package' WHERE `TITLE`='精洗打蜡套餐';
UPDATE `mt_banner` SET `TITLE_EN`='New Customer Trial Coupon' WHERE `TITLE`='新客体验券';
UPDATE `mt_banner` SET `TITLE_EN`='Workshop Showcase'         WHERE `TITLE`='施工车间展示';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day Carnival'       WHERE `TITLE`='会员日狂欢';

-- 文章
UPDATE `mt_article` SET `TITLE_EN`='Spring Car Care Guide'            WHERE `TITLE`='春季爱车保养指南';
UPDATE `mt_article` SET `TITLE_EN`='Member Exclusive 50% off Car Wash' WHERE `TITLE`='会员专享 洗车5折';
UPDATE `mt_article` SET `TITLE_EN`='Importance of Interior Deep Cleaning' WHERE `TITLE`='内饰深度清洁的重要性';
UPDATE `mt_article` SET `TITLE_EN`='Tire Replacement Cycle Guide'      WHERE `TITLE`='轮胎更换周期说明';
UPDATE `mt_article` SET `TITLE_EN`='Rainy Season Driving Safety Tips'  WHERE `TITLE`='雨季行车安全提示';
UPDATE `mt_article` SET `TITLE_EN`='Member Points Redemption'          WHERE `TITLE`='会员积分兑换';
UPDATE `mt_article` SET `TITLE_EN`='New Store Grand Opening'           WHERE `TITLE`='新店开业钜惠';
UPDATE `mt_article` SET `TITLE_EN`='AC System Cleaning Tips'           WHERE `TITLE`='空调系统清洗常识';

-- 商品
UPDATE `mt_goods` SET `NAME_EN`='3M Heat-insulating Film'       WHERE `NAME`='3M 隔热车膜';
UPDATE `mt_goods` SET `NAME_EN`='70mai Dash Cam'                WHERE `NAME`='70迈行车记录仪';
UPDATE `mt_goods` SET `NAME_EN`='SUV/MPV Car Wash'              WHERE `NAME`='SUV/商务车洗车';
UPDATE `mt_goods` SET `NAME_EN`='Full Hand Wax'                 WHERE `NAME`='全车手工打蜡';
UPDATE `mt_goods` SET `NAME_EN`='Full Paint Polishing'          WHERE `NAME`='全车漆面抛光';
UPDATE `mt_goods` SET `NAME_EN`='Full Ozone Sterilization'      WHERE `NAME`='全车臭氧消毒';
UPDATE `mt_goods` SET `NAME_EN`='Interior Deep Cleaning'        WHERE `NAME`='内饰深度清洗';
UPDATE `mt_goods` SET `NAME_EN`='Interior Leather Care'         WHERE `NAME`='内饰真皮护理';
UPDATE `mt_goods` SET `NAME_EN`='Brake Pad Replacement'         WHERE `NAME`='刹车片更换';
UPDATE `mt_goods` SET `NAME_EN`='Windshield Coating'            WHERE `NAME`='前挡玻璃镀膜';
UPDATE `mt_goods` SET `NAME_EN`='Engine Bay Cleaning'           WHERE `NAME`='发动机舱清洗';
UPDATE `mt_goods` SET `NAME_EN`='Four-wheel Alignment'          WHERE `NAME`='四轮定位';
UPDATE `mt_goods` SET `NAME_EN`='Goodyear Carpet Mat'           WHERE `NAME`='固特异丝圈脚垫';
UPDATE `mt_goods` SET `NAME_EN`='Shell Full Synthetic Oil 4L'   WHERE `NAME`='壳牌全合成机油 4L';
UPDATE `mt_goods` SET `NAME_EN`='Major Service 3 Filters'       WHERE `NAME`='大保养 三滤全换';
UPDATE `mt_goods` SET `NAME_EN`='Minor Service Oil+Filter'      WHERE `NAME`='小保养 机油机滤';
UPDATE `mt_goods` SET `NAME_EN`='Minor Service Package (Oil+Filter)' WHERE `NAME`='小保养套餐(机油+机滤)';
UPDATE `mt_goods` SET `NAME_EN`='Local Scratch Repair'          WHERE `NAME`='局部划痕修复';
UPDATE `mt_goods` SET `NAME_EN`='Seat Refurbishment'            WHERE `NAME`='座椅翻新修复';
UPDATE `mt_goods` SET `NAME_EN`='New Car Formaldehyde Removal'  WHERE `NAME`='新车除甲醛';
UPDATE `mt_goods` SET `NAME_EN`='Standard Car Wash'             WHERE `NAME`='标准洗车';
UPDATE `mt_goods` SET `NAME_EN`='Car Wash 12-ride Card'         WHERE `NAME`='洗车次卡 12次';
UPDATE `mt_goods` SET `NAME_EN`='Paint Decontamination'         WHERE `NAME`='漆面去污处理';
UPDATE `mt_goods` SET `NAME_EN`='Paint Coating Crystal'         WHERE `NAME`='漆面镀晶';
UPDATE `mt_goods` SET `NAME_EN`='Spark Plug Replacement'        WHERE `NAME`='火花塞更换';
UPDATE `mt_goods` SET `NAME_EN`='Windshield Washer Fluid 1.5L'  WHERE `NAME`='玻璃水 1.5L';
UPDATE `mt_goods` SET `NAME_EN`='Windshield Washer Fluid 2L'    WHERE `NAME`='玻璃水 2L';
UPDATE `mt_goods` SET `NAME_EN`='AC Filter Replacement'         WHERE `NAME`='空调滤芯更换';
UPDATE `mt_goods` SET `NAME_EN`='AC System Cleaning'            WHERE `NAME`='空调系统清洗';
UPDATE `mt_goods` SET `NAME_EN`='Michelin Tire 205/55R16'       WHERE `NAME`='米其林轮胎 205/55R16';
UPDATE `mt_goods` SET `NAME_EN`='Premium Wash & Wax'            WHERE `NAME`='精洗打蜡';
UPDATE `mt_goods` SET `NAME_EN`='Premium Car Wash'              WHERE `NAME`='精致洗车';
UPDATE `mt_goods` SET `NAME_EN`='Battery Replacement'           WHERE `NAME`='蓄电池更换';
UPDATE `mt_goods` SET `NAME_EN`='Body Wax Care'                 WHERE `NAME`='车身打蜡护理';
UPDATE `mt_goods` SET `NAME_EN`='Car Fast Charger'              WHERE `NAME`='车载快充充电器';
UPDATE `mt_goods` SET `NAME_EN`='Car Wireless Vacuum'           WHERE `NAME`='车载无线吸尘器';
UPDATE `mt_goods` SET `NAME_EN`='Wheel Deep Cleaning'           WHERE `NAME`='轮毂深度清洁';
UPDATE `mt_goods` SET `NAME_EN`='Tire Replacement Single'       WHERE `NAME`='轮胎更换 单条';
UPDATE `mt_goods` SET `NAME_EN`='Roof Velvet Surface Cleaning'  WHERE `NAME`='顶棚绒面清洗';

-- ============================ 餐饮 bahar-catering ============================
USE `bahar-catering`;

-- 分类
UPDATE `mt_goods_cate` SET `NAME_EN`='Signature Hot Dishes'  WHERE `NAME`='招牌热菜';
UPDATE `mt_goods_cate` SET `NAME_EN`='Cold Dishes & Marinades' WHERE `NAME`='凉菜卤味';
UPDATE `mt_goods_cate` SET `NAME_EN`='Staple & Soup'         WHERE `NAME`='主食汤羹';
UPDATE `mt_goods_cate` SET `NAME_EN`='Drinks & Beverages'    WHERE `NAME`='酒水饮品';

-- 会员等级
UPDATE `mt_user_grade` SET `NAME_EN`='Regular'           WHERE `NAME`='普通会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Silver'            WHERE `NAME`='银卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Gold'              WHERE `NAME`='金卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Diamond'           WHERE `NAME`='钻石会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Tasty Monthly Card'   WHERE `NAME`='美味月卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Enjoy Quarterly Card' WHERE `NAME`='畅享季卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Supreme Annual Card'  WHERE `NAME`='至尊年卡';

-- 门店
UPDATE `mt_store` SET `NAME_EN`='Demo F&B HQ Store'      WHERE `NAME`='演示餐饮总店';
UPDATE `mt_store` SET `NAME_EN`='East Store'             WHERE `NAME`='城东分店';
UPDATE `mt_store` SET `NAME_EN`='New District Flagship'  WHERE `NAME`='新区旗舰店';

-- 券
UPDATE `mt_coupon` SET `NAME_EN`='¥20 off over ¥100 Coupon'     WHERE `NAME`='满100减20券';
UPDATE `mt_coupon` SET `NAME_EN`='20% off Breakfast Coupon'     WHERE `NAME`='早餐8折券';
UPDATE `mt_coupon` SET `NAME_EN`='¥500 Stored-value Card'       WHERE `NAME`='500元储值卡';
UPDATE `mt_coupon` SET `NAME_EN`='New Customer Exclusive Coupon' WHERE `NAME`='新客专享券';
UPDATE `mt_coupon` SET `NAME_EN`='¥20 off over ¥100 Coupon'     WHERE `NAME`='满100减20';
UPDATE `mt_coupon` SET `NAME_EN`='Member Day Coupon'           WHERE `NAME`='会员日券';
UPDATE `mt_coupon` SET `NAME_EN`='Holiday Gift Pack Coupon'    WHERE `NAME`='节日礼包券';

-- 轮播
UPDATE `mt_banner` SET `TITLE_EN`='Signature Dishes'             WHERE `TITLE`='招牌菜推荐';
UPDATE `mt_banner` SET `TITLE_EN`='Member Top-up Gift'          WHERE `TITLE`='会员储值礼';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day 10% Off Storewide' WHERE `TITLE`='会员日全场9折';
UPDATE `mt_banner` SET `TITLE_EN`='Top-up Free Gift'            WHERE `TITLE`='储值送好礼';
UPDATE `mt_banner` SET `TITLE_EN`='Restaurant Environment Showcase' WHERE `TITLE`='餐厅环境展示';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day Carnival'         WHERE `TITLE`='会员日狂欢';

-- 文章
UPDATE `mt_article` SET `TITLE_EN`='New Arrivals Summer Refreshing Menu' WHERE `TITLE`='新品上市 夏季清爽菜系';
UPDATE `mt_article` SET `TITLE_EN`='Member Day 10% Off Storewide'        WHERE `TITLE`='会员日 全场9折';
UPDATE `mt_article` SET `TITLE_EN`='Our Signature Dishes'                WHERE `TITLE`='本店招牌菜推荐';
UPDATE `mt_article` SET `TITLE_EN`='Delivery Notes'                      WHERE `TITLE`='外卖配送说明';
UPDATE `mt_article` SET `TITLE_EN`='Private Room Booking Guide'          WHERE `TITLE`='包间预订须知';
UPDATE `mt_article` SET `TITLE_EN`='Member Top-up Discount'              WHERE `TITLE`='会员储值优惠';
UPDATE `mt_article` SET `TITLE_EN`='Food Safety Notice'                  WHERE `TITLE`='食品安全公示';
UPDATE `mt_article` SET `TITLE_EN`='Holiday Business Hours'              WHERE `TITLE`='节日营业时间';

-- 商品
UPDATE `mt_goods` SET `NAME_EN`='Northeast Cold Noodles'       WHERE `NAME`='东北大拉皮';
UPDATE `mt_goods` SET `NAME_EN`='Simiao Steamed Rice'         WHERE `NAME`='丝苗白米饭';
UPDATE `mt_goods` SET `NAME_EN`='Chilled Beer'                WHERE `NAME`='冰镇啤酒';
UPDATE `mt_goods` SET `NAME_EN`='Chilled Sour Plum Drink'     WHERE `NAME`='冰镇酸梅汤';
UPDATE `mt_goods` SET `NAME_EN`='Cold Kelp Salad'             WHERE `NAME`='凉拌海带丝';
UPDATE `mt_goods` SET `NAME_EN`='Cold Cucumber Salad'         WHERE `NAME`='凉拌黄瓜';
UPDATE `mt_goods` SET `NAME_EN`='Cold Black Fungus Salad'     WHERE `NAME`='凉拌黑木耳';
UPDATE `mt_goods` SET `NAME_EN`='Couple Combo Voucher'        WHERE `NAME`='双人套餐券';
UPDATE `mt_goods` SET `NAME_EN`='Poached Chicken with Chili Sauce' WHERE `NAME`='口水鸡';
UPDATE `mt_goods` SET `NAME_EN`='Coca-Cola'                   WHERE `NAME`='可口可乐';
UPDATE `mt_goods` SET `NAME_EN`='Twice-cooked Pork'           WHERE `NAME`='回锅肉';
UPDATE `mt_goods` SET `NAME_EN`='Spicy Beef Slices'           WHERE `NAME`='夫妻肺片';
UPDATE `mt_goods` SET `NAME_EN`='Kung Pao Chicken'            WHERE `NAME`='宫保鸡丁';
UPDATE `mt_goods` SET `NAME_EN`='Dry Pot Bullfrog'            WHERE `NAME`='干锅牛蛙';
UPDATE `mt_goods` SET `NAME_EN`='Handmade Pork Dumplings'     WHERE `NAME`='手工猪肉水饺';
UPDATE `mt_goods` SET `NAME_EN`='Handmade Steamed Bun'        WHERE `NAME`='手工老面馒头';
UPDATE `mt_goods` SET `NAME_EN`='Hand-smacked Cucumber'       WHERE `NAME`='手拍黄瓜';
UPDATE `mt_goods` SET `NAME_EN`='Yangzhou Fried Rice'         WHERE `NAME`='扬州炒饭';
UPDATE `mt_goods` SET `NAME_EN`='Lemon Honey Water'           WHERE `NAME`='柠檬蜂蜜水';
UPDATE `mt_goods` SET `NAME_EN`='Osmanthus Sour Plum Drink'  WHERE `NAME`='桂花酸梅汤';
UPDATE `mt_goods` SET `NAME_EN`='Boiled Fish Slices'          WHERE `NAME`='水煮鱼片';
UPDATE `mt_goods` SET `NAME_EN`='Pickled Pepper Chicken Feet' WHERE `NAME`='泡椒凤爪';
UPDATE `mt_goods` SET `NAME_EN`='Stir-fried Vegetables'       WHERE `NAME`='清炒时蔬';
UPDATE `mt_goods` SET `NAME_EN`='Steamed Sea Bass'            WHERE `NAME`='清蒸鲈鱼';
UPDATE `mt_goods` SET `NAME_EN`='Wong Lo Kat'                 WHERE `NAME`='王老吉';
UPDATE `mt_goods` SET `NAME_EN`='Fresh Hot Soy Milk'          WHERE `NAME`='现磨热豆浆';
UPDATE `mt_goods` SET `NAME_EN`='Tomato Beef Brisket Pot'     WHERE `NAME`='番茄牛腩煲';
UPDATE `mt_goods` SET `NAME_EN`='Century Egg Tofu'            WHERE `NAME`='皮蛋豆腐';
UPDATE `mt_goods` SET `NAME_EN`='Braised Pork Belly'          WHERE `NAME`='秘制红烧肉';
UPDATE `mt_goods` SET `NAME_EN`='Claypot Rice with Sausage'   WHERE `NAME`='腊味煲仔饭';
UPDATE `mt_goods` SET `NAME_EN`='Mushroom Health Soup'        WHERE `NAME`='菌菇养生汤';
UPDATE `mt_goods` SET `NAME_EN`='Scallion Oil Noodles'        WHERE `NAME`='葱油拌面';
UPDATE `mt_goods` SET `NAME_EN`='Garlic Vermicelli Scallop'   WHERE `NAME`='蒜蓉粉丝扇贝';
UPDATE `mt_goods` SET `NAME_EN`='Shrimp Wonton'               WHERE `NAME`='虾仁小馄饨';
UPDATE `mt_goods` SET `NAME_EN`='Plain Noodle Soup'           WHERE `NAME`='阳春面';
UPDATE `mt_goods` SET `NAME_EN`='Sprite'                      WHERE `NAME`='雪碧';
UPDATE `mt_goods` SET `NAME_EN`='Fresh Orange Juice'          WHERE `NAME`='鲜榨橙汁';
UPDATE `mt_goods` SET `NAME_EN`='Mapo Tofu'                   WHERE `NAME`='麻婆豆腐';

-- ============================ 康养 bahar-health ============================
USE `bahar-health`;

-- 分类
UPDATE `mt_goods_cate` SET `NAME_EN`='Facial Care'     WHERE `NAME`='面部护理';
UPDATE `mt_goods_cate` SET `NAME_EN`='Body Therapy'    WHERE `NAME`='身体理疗';
UPDATE `mt_goods_cate` SET `NAME_EN`='Wellness Care'   WHERE `NAME`='养生保健';
UPDATE `mt_goods_cate` SET `NAME_EN`='Health Products' WHERE `NAME`='健康产品';

-- 会员等级
UPDATE `mt_user_grade` SET `NAME_EN`='Regular'             WHERE `NAME`='普通会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Silver'              WHERE `NAME`='银卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Gold'                WHERE `NAME`='金卡会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Diamond'             WHERE `NAME`='钻石会员';
UPDATE `mt_user_grade` SET `NAME_EN`='Wellness Monthly Card' WHERE `NAME`='养生月卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Therapy Quarterly Card' WHERE `NAME`='理疗季卡';
UPDATE `mt_user_grade` SET `NAME_EN`='Premium Annual Card' WHERE `NAME`='尊享年卡';

-- 门店
UPDATE `mt_store` SET `NAME_EN`='Demo Wellness HQ Store'   WHERE `NAME`='演示康养总店';
UPDATE `mt_store` SET `NAME_EN`='East Store'               WHERE `NAME`='城东分店';
UPDATE `mt_store` SET `NAME_EN`='New District Flagship'    WHERE `NAME`='新区旗舰店';

-- 券
UPDATE `mt_coupon` SET `NAME_EN`='¥50 Newcomer Trial Coupon'     WHERE `NAME`='新人体验券50元';
UPDATE `mt_coupon` SET `NAME_EN`='¥80 off over ¥500 Coupon'      WHERE `NAME`='满500减80券';
UPDATE `mt_coupon` SET `NAME_EN`='¥2000 Stored-value Card'       WHERE `NAME`='2000元储值卡';
UPDATE `mt_coupon` SET `NAME_EN`='New Customer Exclusive Coupon' WHERE `NAME`='新客专享券';
UPDATE `mt_coupon` SET `NAME_EN`='¥20 off over ¥100 Coupon'      WHERE `NAME`='满100减20';
UPDATE `mt_coupon` SET `NAME_EN`='Member Day Coupon'             WHERE `NAME`='会员日券';
UPDATE `mt_coupon` SET `NAME_EN`='Holiday Gift Pack Coupon'      WHERE `NAME`='节日礼包券';

-- 轮播
UPDATE `mt_banner` SET `TITLE_EN`='Opening Special'            WHERE `TITLE`='开业特惠';
UPDATE `mt_banner` SET `TITLE_EN`='Top-up Bonus'               WHERE `TITLE`='储值返赠';
UPDATE `mt_banner` SET `TITLE_EN`='Member Care Package'        WHERE `TITLE`='会员护理套餐';
UPDATE `mt_banner` SET `TITLE_EN`='New Customer Trial ¥98'     WHERE `TITLE`='新客体验98元';
UPDATE `mt_banner` SET `TITLE_EN`='Wellness Tea Free Drink'    WHERE `TITLE`='养生茶饮赠饮';
UPDATE `mt_banner` SET `TITLE_EN`='Store Environment Showcase' WHERE `TITLE`='门店环境展示';
UPDATE `mt_banner` SET `TITLE_EN`='Member Day Carnival'        WHERE `TITLE`='会员日狂欢';

-- 文章
UPDATE `mt_article` SET `TITLE_EN`='Spring Wellness Guide'          WHERE `TITLE`='春季养生指南';
UPDATE `mt_article` SET `TITLE_EN`='Member Exclusive Care Package'  WHERE `TITLE`='会员专享 护理套餐';
UPDATE `mt_article` SET `TITLE_EN`='Importance of Shoulder & Neck Care' WHERE `TITLE`='肩颈保养的重要性';
UPDATE `mt_article` SET `TITLE_EN`='Benefits of Moxibustion Wellness'  WHERE `TITLE`='艾灸养生的功效';
UPDATE `mt_article` SET `TITLE_EN`='New Member Trial Event'        WHERE `TITLE`='新会员体验活动';
UPDATE `mt_article` SET `TITLE_EN`='Member Points Redemption'      WHERE `TITLE`='会员积分兑换';
UPDATE `mt_article` SET `TITLE_EN`='Healthy Diet Advice'           WHERE `TITLE`='健康饮食建议';
UPDATE `mt_article` SET `TITLE_EN`='Holiday Appointment Reminder'  WHERE `TITLE`='节假日预约提醒';

-- 商品
UPDATE `mt_goods` SET `NAME_EN`='10-session Therapy Card'       WHERE `NAME`='10次理疗次卡';
UPDATE `mt_goods` SET `NAME_EN`='TCM Moxibustion Care'          WHERE `NAME`='中医艾灸调理';
UPDATE `mt_goods` SET `NAME_EN`='TCM Herbal Fumigation'         WHERE `NAME`='中药熏蒸';
UPDATE `mt_goods` SET `NAME_EN`='TCM Herbal Foot Spa'           WHERE `NAME`='中药足疗';
UPDATE `mt_goods` SET `NAME_EN`='TCM Herbal Foot Spa 60min'     WHERE `NAME`='中药足疗 60分钟';
UPDATE `mt_goods` SET `NAME_EN`='Latex Neck Pillow'             WHERE `NAME`='乳胶护颈枕';
UPDATE `mt_goods` SET `NAME_EN`='Sub-health Regulation'         WHERE `NAME`='亚健康调理';
UPDATE `mt_goods` SET `NAME_EN`='Ergonomic Lumbar Cushion'      WHERE `NAME`='人体工学护腰垫';
UPDATE `mt_goods` SET `NAME_EN`='Constitution Assessment Care'  WHERE `NAME`='体质辨识调理';
UPDATE `mt_goods` SET `NAME_EN`='Full Body Tuina 90min'         WHERE `NAME`='全身推拿 90分钟';
UPDATE `mt_goods` SET `NAME_EN`='Full Body Relaxation Massage'  WHERE `NAME`='全身放松按摩';
UPDATE `mt_goods` SET `NAME_EN`='Wellness Flower Tea Gift Box'  WHERE `NAME`='养生花茶礼盒';
UPDATE `mt_goods` SET `NAME_EN`='Wellness Herbal Tea'           WHERE `NAME`='养生花草茶';
UPDATE `mt_goods` SET `NAME_EN`='Acne Clearing Facial'          WHERE `NAME`='净颜祛痘护理';
UPDATE `mt_goods` SET `NAME_EN`='Gua Sha Detox'                 WHERE `NAME`='刮痧排毒';
UPDATE `mt_goods` SET `NAME_EN`='Compound Probiotics'           WHERE `NAME`='复合益生菌';
UPDATE `mt_goods` SET `NAME_EN`='Bubble Deep Cleansing'         WHERE `NAME`='小气泡深层清洁';
UPDATE `mt_goods` SET `NAME_EN`='Anti-aging Firming Care'       WHERE `NAME`='抗衰紧致护理';
UPDATE `mt_goods` SET `NAME_EN`='Cupping Dampness Removal'      WHERE `NAME`='拔罐祛湿';
UPDATE `mt_goods` SET `NAME_EN`='Qi & Blood Tonic Care'         WHERE `NAME`='气血双补调理';
UPDATE `mt_goods` SET `NAME_EN`='Deep Cleansing Bubble'         WHERE `NAME`='深层清洁小气泡';
UPDATE `mt_goods` SET `NAME_EN`='Deep Cleansing Care'           WHERE `NAME`='深层清洁护理';
UPDATE `mt_goods` SET `NAME_EN`='Deep Sea Fish Oil Softgel'     WHERE `NAME`='深海鱼油软胶囊';
UPDATE `mt_goods` SET `NAME_EN`='Hyaluronic Deep Hydration'    WHERE `NAME`='玻尿酸深度补水';
UPDATE `mt_goods` SET `NAME_EN`='Hyaluronic Hydrating Care'    WHERE `NAME`='玻尿酸补水保湿';
UPDATE `mt_goods` SET `NAME_EN`='Eye Fine Care'                 WHERE `NAME`='眼部精细护理';
UPDATE `mt_goods` SET `NAME_EN`='Sleep Improvement Care'        WHERE `NAME`='睡眠改善调理';
UPDATE `mt_goods` SET `NAME_EN`='Essential Oil Back Massage'   WHERE `NAME`='精油开背';
UPDATE `mt_goods` SET `NAME_EN`='Meridian Dredging'            WHERE `NAME`='经络疏通';
UPDATE `mt_goods` SET `NAME_EN`='Vitamin C Tablets'            WHERE `NAME`='维生素C片';
UPDATE `mt_goods` SET `NAME_EN`='Whitening Spot Care'          WHERE `NAME`='美白淡斑护理';
UPDATE `mt_goods` SET `NAME_EN`='Liver & Gallbladder Care'     WHERE `NAME`='肝胆调理';
UPDATE `mt_goods` SET `NAME_EN`='Shoulder & Neck Dredging'     WHERE `NAME`='肩颈疏通';
UPDATE `mt_goods` SET `NAME_EN`='Shoulder & Neck Dredging 45min' WHERE `NAME`='肩颈疏通 45分钟';
UPDATE `mt_goods` SET `NAME_EN`='Collagen Peptide Drink'       WHERE `NAME`='胶原蛋白肽饮';
UPDATE `mt_goods` SET `NAME_EN`='Spleen & Stomach Care'        WHERE `NAME`='脾胃调理';
UPDATE `mt_goods` SET `NAME_EN`='Lumbar Care'                  WHERE `NAME`='腰椎调理';
UPDATE `mt_goods` SET `NAME_EN`='Moxibustion Wellness'         WHERE `NAME`='艾灸养生';
UPDATE `mt_goods` SET `NAME_EN`='Mugwort Foot Bath Pack'       WHERE `NAME`='艾草足浴包';
UPDATE `mt_goods` SET `NAME_EN`='Herbal Fumigation Therapy'    WHERE `NAME`='草本熏蒸理疗';
UPDATE `mt_goods` SET `NAME_EN`='Herbal Foot Bath Pack 10pk'  WHERE `NAME`='草本足浴包 10袋';
UPDATE `mt_goods` SET `NAME_EN`='Facial Meridian Dredging'    WHERE `NAME`='面部拨筋疏通';
UPDATE `mt_goods` SET `NAME_EN`='Gold Renewal Treatment'      WHERE `NAME`='黄金焕肤护理';

SELECT '24-seed-name-en.sql executed.' AS result;
