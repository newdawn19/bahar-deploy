-- 汽车库补车辆模块权限节点（2026-10-03 复检 N13/N4）：
-- 车辆模块是后来移植进 baharCar 的，当初的权限脚本没覆盖，
-- t_source 里连"车辆管理"一级节点都没有 —— 这就是后台菜单挂不上的根因。
-- ID 段 1130-1132（当前 bahar-car 最大 source_id=1121，无冲突）。
-- 幂等：先删后插。
USE `bahar-car`;
SET NAMES utf8mb4;

DELETE FROM t_duty_source WHERE duty_source_id BETWEEN 900101 AND 900199;
DELETE FROM t_source WHERE source_id IN (1130, 1131, 1132);

INSERT INTO t_source (merchant_id, source_id, source_name, source_code, path, ename,
                      new_icon, status, source_level, source_style, is_menu, description,
                      parent_id, is_log, icon) VALUES
(1, 1130, '车辆管理', 'vehicle', 'vehicle', 'Vehicle', 'el-icon-menu', 'A', 1, '1130', 1, '车辆管理', 0, 0, ''),
(1, 1131, '车辆档案', 'vehicle_index', 'vehicle/index', 'Index', '', 'A', 2, '1130,1131', 1, '车辆档案', 1130, 0, ''),
(1, 1132, '车辆服务单', 'vehicleOrder_index', 'vehicleOrder/index', 'Index', '', 'A', 2, '1130,1132', 1, '车辆服务单', 1130, 0, '');

-- 超级管理员（duty 1）授权到这三个节点
INSERT INTO t_duty_source (duty_source_id, duty_id, source_id) VALUES
(900101, 1, 1130),
(900102, 1, 1131),
(900103, 1, 1132);
