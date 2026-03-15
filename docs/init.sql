-- SmartAD Engine 数据库初始化脚本
-- 数据库：MySQL 8.0+
-- 字符集：utf8mb4

CREATE DATABASE IF NOT EXISTS smartad DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smartad;

-- =====================================================================
-- 1. 用户表
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_user` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username`    VARCHAR(64)  NOT NULL COMMENT '用户名',
  `password`    VARCHAR(255) NOT NULL COMMENT 'BCrypt密码',
  `role`        VARCHAR(32)  NOT NULL DEFAULT 'admin' COMMENT '角色: admin',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 默认管理员账号: admin / admin123
-- BCrypt hash of "admin123"
INSERT INTO `smartad_user` (`username`, `password`, `role`) VALUES
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5Eu', 'admin');

-- =====================================================================
-- 2. 指令表
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_command` (
  `id`           BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键',
  `command_id`   VARCHAR(32)   NOT NULL COMMENT '业务指令ID: CMD-YYYYMMDD-NNNN',
  `command_text` TEXT          NOT NULL COMMENT '原始自然语言指令',
  `status`       VARCHAR(32)   NOT NULL DEFAULT 'pending'
                   COMMENT '状态: pending/processing/waiting_reply/waiting_replied/completed/failed',
  `ai_question`  TEXT          COMMENT 'AI追问内容',
  `user_reply`   TEXT          COMMENT '用户回复内容',
  `operator_id`  BIGINT        NOT NULL COMMENT '操作员ID',
  `created_at`   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_command_id` (`command_id`),
  KEY `idx_status` (`status`),
  KEY `idx_operator` (`operator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投放指令表';

-- =====================================================================
-- 3. 策略表
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_strategy` (
  `id`           BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键',
  `strategy_id`  VARCHAR(32)    NOT NULL COMMENT '业务策略ID: STR-YYYYMMDD-NNNN',
  `command_id`   VARCHAR(32)    NOT NULL COMMENT '来源指令ID',
  `crowd_id`     BIGINT         NOT NULL COMMENT '人群画像ID',
  `crowd_tag`    VARCHAR(64)    NOT NULL COMMENT '人群标签',
  `channel`      VARCHAR(32)    NOT NULL COMMENT '渠道: douyin/kuaishou/weibo/toutiao/baidu',
  `budget_day`   DECIMAL(10,2)  NOT NULL COMMENT '日预算(元)',
  `bid_price`    INT            NOT NULL COMMENT '出价(分)',
  `status`       VARCHAR(32)    NOT NULL DEFAULT 'pending_confirm'
                   COMMENT '状态: pending_confirm/risk_pending/active/paused/offline/rejected/processing',
  `ai_reason`    TEXT           COMMENT 'AI生成理由',
  `ai_score`     INT            COMMENT 'AI评分 0-100',
  `adjust_type`  VARCHAR(32)    COMMENT '最近调整类型',
  `adjust_reason` TEXT          COMMENT '最近调整理由',
  `channel_ad_id` VARCHAR(128)  COMMENT '渠道广告ID',
  `created_at`   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_strategy_id` (`strategy_id`),
  KEY `idx_command_id` (`command_id`),
  KEY `idx_status` (`status`),
  KEY `idx_crowd_channel` (`crowd_tag`, `channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告投放策略表';

-- =====================================================================
-- 4. 人群画像表
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_crowd` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  `crowd_tag`   VARCHAR(64)  NOT NULL COMMENT '人群标签（唯一标识）',
  `description` VARCHAR(255) COMMENT '描述',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_crowd_tag` (`crowd_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人群画像表';

INSERT INTO `smartad_crowd` (`crowd_tag`, `description`) VALUES
('young_fashion', '18-28岁时尚女性，对服饰美妆敏感，转化率高'),
('middle_income', '30-45岁中等收入家庭，偏品质消费，客单价高'),
('senior_tech', '45岁以上科技爱好者，忠诚度高，ROI稳定'),
('student', '18-25岁在校学生，价格敏感，活跃度高'),
('enterprise', 'B端企业采购决策人，客单价极高');

-- =====================================================================
-- 5. 报表表（含模拟历史数据）
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_report` (
  `id`          BIGINT         NOT NULL AUTO_INCREMENT,
  `strategy_id` VARCHAR(32)    NOT NULL COMMENT '策略ID',
  `crowd_tag`   VARCHAR(64)    NOT NULL COMMENT '人群标签',
  `channel`     VARCHAR(32)    NOT NULL COMMENT '渠道',
  `report_date` DATE           NOT NULL COMMENT '报表日期',
  `impressions` BIGINT         NOT NULL DEFAULT 0 COMMENT '曝光量',
  `clicks`      BIGINT         NOT NULL DEFAULT 0 COMMENT '点击量',
  `ctr`         DECIMAL(8,6)   NOT NULL DEFAULT 0 COMMENT '点击率',
  `cost`        DECIMAL(10,2)  NOT NULL DEFAULT 0 COMMENT '消耗金额(元)',
  `conversions` INT            NOT NULL DEFAULT 0 COMMENT '转化量',
  `roi`         DECIMAL(8,4)   NOT NULL DEFAULT 0 COMMENT 'ROI',
  `created_at`  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_strategy_date` (`strategy_id`, `report_date`),
  KEY `idx_crowd_channel` (`crowd_tag`, `channel`),
  KEY `idx_report_date` (`report_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投放报表表';

-- 预置历史投放模拟数据（用于 AI 历史效果参考）
-- 模拟策略ID前缀使用 HIST-，不影响真实策略
INSERT INTO `smartad_strategy` (`strategy_id`,`command_id`,`crowd_id`,`crowd_tag`,`channel`,`budget_day`,`bid_price`,`status`,`ai_reason`) VALUES
('HIST-20260101-0001','CMD-20260101-0001',1,'young_fashion','douyin',500.00,120,'offline','历史模拟数据'),
('HIST-20260101-0002','CMD-20260101-0001',2,'middle_income','baidu',800.00,200,'offline','历史模拟数据'),
('HIST-20260101-0003','CMD-20260101-0001',3,'senior_tech','toutiao',300.00,80,'offline','历史模拟数据'),
('HIST-20260101-0004','CMD-20260101-0002',4,'student','kuaishou',200.00,60,'offline','历史模拟数据'),
('HIST-20260101-0005','CMD-20260101-0002',1,'young_fashion','weibo',400.00,150,'offline','历史模拟数据');

INSERT INTO `smartad_report` (`strategy_id`,`crowd_tag`,`channel`,`report_date`,`impressions`,`clicks`,`ctr`,`cost`,`conversions`,`roi`) VALUES
-- young_fashion + douyin (历史7天)
('HIST-20260101-0001','young_fashion','douyin','2026-01-01',52000,1352,0.026,498.50,68,2.12),
('HIST-20260101-0001','young_fashion','douyin','2026-01-02',58000,1624,0.028,499.80,81,2.35),
('HIST-20260101-0001','young_fashion','douyin','2026-01-03',49000,1274,0.026,487.20,63,1.98),
-- middle_income + baidu
('HIST-20260101-0002','middle_income','baidu','2026-01-01',12000,480,0.040,795.00,42,3.20),
('HIST-20260101-0002','middle_income','baidu','2026-01-02',11500,460,0.040,799.50,38,2.95),
-- senior_tech + toutiao
('HIST-20260101-0003','senior_tech','toutiao','2026-01-01',28000,504,0.018,298.00,31,2.45),
('HIST-20260101-0003','senior_tech','toutiao','2026-01-02',31000,589,0.019,300.00,35,2.78),
-- student + kuaishou
('HIST-20260101-0004','student','kuaishou','2026-01-01',45000,720,0.016,198.00,52,3.10),
('HIST-20260101-0004','student','kuaishou','2026-01-02',47000,799,0.017,200.00,60,3.45),
-- young_fashion + weibo
('HIST-20260101-0005','young_fashion','weibo','2026-01-01',18000,504,0.028,399.20,29,1.65),
('HIST-20260101-0005','young_fashion','weibo','2026-01-02',19500,546,0.028,400.00,32,1.80),
-- 补充低效数据（用于触发告警场景测试）
('HIST-20260101-0003','senior_tech','toutiao','2026-01-03',15000,112,0.007,295.00,8,0.62),
('HIST-20260101-0004','student','kuaishou','2026-01-03',21000,84,0.004,199.00,5,0.45);

-- =====================================================================
-- 6. 告警表
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_alert` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT,
  `alert_id`      VARCHAR(32)  NOT NULL COMMENT '业务告警ID: ALT-YYYYMMDD-NNNN',
  `strategy_id`   VARCHAR(32)  NOT NULL COMMENT '策略ID',
  `alert_type`    VARCHAR(32)  NOT NULL COMMENT '类型: low_ctr/low_roi/budget_overrun/no_conversion/abnormal_cost',
  `alert_level`   VARCHAR(16)  NOT NULL DEFAULT 'warning' COMMENT '级别: info/warning/critical',
  `alert_message` TEXT         NOT NULL COMMENT '告警消息',
  `status`        VARCHAR(16)  NOT NULL DEFAULT 'active' COMMENT '状态: active/confirmed',
  `confirmed_at`  DATETIME     COMMENT '确认时间',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alert_id` (`alert_id`),
  KEY `idx_strategy_id` (`strategy_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警表';

-- =====================================================================
-- 7. 日志表（第一阶段替代ClickHouse）
-- =====================================================================
CREATE TABLE IF NOT EXISTS `smartad_log` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `event_type`  VARCHAR(32)  NOT NULL COMMENT '事件类型: click/impression/conversion',
  `strategy_id` VARCHAR(32)  COMMENT '策略ID',
  `channel`     VARCHAR(32)  COMMENT '渠道',
  `ad_slot`     VARCHAR(64)  COMMENT '广告位',
  `device_id`   VARCHAR(128) COMMENT '设备标识',
  `user_id`     BIGINT       COMMENT '用户ID',
  `extra`       JSON         COMMENT '扩展字段',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_strategy_id` (`strategy_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行为日志表（第一阶段临时，第三阶段迁移至ClickHouse）';
