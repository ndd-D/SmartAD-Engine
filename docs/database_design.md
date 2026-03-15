# SmartAD Engine 数据库设计文档

## 一、概览

| 表名 | 说明 |
|------|------|
| `smartad_user` | 系统用户（管理员） |
| `smartad_command` | 投放指令（自然语言→AI解析） |
| `smartad_strategy` | 广告投放策略（AI生成，人工审核） |
| `smartad_crowd` | 人群画像字典 |
| `smartad_report` | 投放效果报表（日粒度） |
| `smartad_alert` | 投放告警 |
| `smartad_log` | 用户行为日志（第一阶段用MySQL，第三阶段迁ClickHouse） |

---

## 二、表详细设计

### 2.1 smartad_user（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 主键 |
| username | VARCHAR(64) UNIQUE | 用户名 |
| password | VARCHAR(255) | BCrypt密码 |
| role | VARCHAR(32) | 角色（admin） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

### 2.2 smartad_command（投放指令表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 主键 |
| command_id | VARCHAR(32) UNIQUE | 业务ID: `CMD-YYYYMMDD-NNNN` |
| command_text | TEXT | 原始自然语言指令 |
| status | VARCHAR(32) | pending / processing / waiting_reply / waiting_replied / completed / failed |
| ai_question | TEXT | AI追问内容 |
| user_reply | TEXT | 用户回复内容 |
| operator_id | BIGINT | 操作员ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**状态流转：**
```
pending → processing → completed
                    ↓
              waiting_reply ← 需追问
                    ↓ 用户回复
              waiting_replied → processing → completed
                                                ↓
                                             failed
```

---

### 2.3 smartad_strategy（策略表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 主键 |
| strategy_id | VARCHAR(32) UNIQUE | 业务ID: `STR-YYYYMMDD-NNNN` |
| command_id | VARCHAR(32) | 来源指令ID |
| crowd_id | BIGINT | 人群画像ID |
| crowd_tag | VARCHAR(64) | 人群标签 |
| channel | VARCHAR(32) | 渠道标识 |
| budget_day | DECIMAL(10,2) | 日预算（元） |
| bid_price | INT | 出价（分） |
| status | VARCHAR(32) | 策略状态（见下） |
| ai_reason | TEXT | AI生成理由 |
| ai_score | INT | AI健康评分 0-100 |
| adjust_type | VARCHAR(32) | 最近调整类型 |
| adjust_reason | TEXT | 最近调整理由 |
| channel_ad_id | VARCHAR(128) | 渠道侧广告ID |

**策略状态：**

| 状态值 | 含义 |
|--------|------|
| pending_confirm | 待人工确认（普通策略） |
| risk_pending | 高风险待人工确认 |
| processing | AI处理中 |
| active | 投放中 |
| paused | 已暂停 |
| offline | 已下线 |
| rejected | 已拒绝 |

**高风险阈值：** 日预算 > ¥5000 或出价 > 5000分（¥50）

---

### 2.4 smartad_crowd（人群画像表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 主键 |
| crowd_tag | VARCHAR(64) UNIQUE | 人群唯一标签 |
| description | VARCHAR(255) | 人群描述 |

**预置数据：**

| crowd_tag | 描述 |
|-----------|------|
| young_fashion | 18-28岁时尚女性 |
| middle_income | 30-45岁中等收入家庭 |
| senior_tech | 45岁以上科技爱好者 |
| student | 18-25岁在校学生 |
| enterprise | B端企业采购决策人 |

---

### 2.5 smartad_report（报表表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 主键 |
| strategy_id | VARCHAR(32) | 策略ID |
| crowd_tag | VARCHAR(64) | 人群标签 |
| channel | VARCHAR(32) | 渠道 |
| report_date | DATE | 报表日期 |
| impressions | BIGINT | 曝光量 |
| clicks | BIGINT | 点击量 |
| ctr | DECIMAL(8,6) | 点击率 |
| cost | DECIMAL(10,2) | 消耗（元） |
| conversions | INT | 转化量 |
| roi | DECIMAL(8,4) | ROI |

唯一索引：`(strategy_id, report_date)`

---

### 2.6 smartad_alert（告警表）

| 字段 | 类型 | 说明 |
|------|------|------|
| alert_id | VARCHAR(32) | 业务ID: `ALT-YYYYMMDD-NNNN` |
| strategy_id | VARCHAR(32) | 关联策略ID |
| alert_type | VARCHAR(32) | low_ctr / low_roi / budget_overrun / no_conversion / abnormal_cost |
| alert_level | VARCHAR(16) | info / warning / critical |
| alert_message | TEXT | 告警描述 |
| status | VARCHAR(16) | active（未处理）/ confirmed（已确认） |
| confirmed_at | DATETIME | 确认时间 |

---

### 2.7 smartad_log（行为日志表）

> 第一阶段使用 MySQL 存储，第三阶段迁移至 ClickHouse。

| 字段 | 类型 | 说明 |
|------|------|------|
| event_type | VARCHAR(32) | click / impression / conversion |
| strategy_id | VARCHAR(32) | 关联策略ID |
| channel | VARCHAR(32) | 渠道 |
| ad_slot | VARCHAR(64) | 广告位 |
| device_id | VARCHAR(128) | 设备标识 |
| user_id | BIGINT | 用户ID（可空） |
| extra | JSON | 扩展字段 |

---

## 三、ID 生成规则

所有业务 ID 格式：`{前缀}-{YYYYMMDD}-{4位序号}`

| 类型 | 前缀 | 示例 |
|------|------|------|
| 指令 | CMD | CMD-20260313-0001 |
| 策略 | STR | STR-20260313-0001 |
| 告警 | ALT | ALT-20260313-0001 |

序号生成：查当天该类型最大序号 + 1（单机无并发风险）。

---

## 四、ER 关系

```
smartad_user  ──(1:N)── smartad_command
smartad_command ──(1:N)── smartad_strategy
smartad_crowd ──(1:N)── smartad_strategy
smartad_strategy ──(1:N)── smartad_report
smartad_strategy ──(1:N)── smartad_alert
smartad_strategy ──(1:N)── smartad_log
```
