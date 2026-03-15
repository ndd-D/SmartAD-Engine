# 智能广告投放系统（智投引擎）最终版文档合集
## 目录
1. [更新后完整版API开发文档](#一-api开发文档-智投引擎-完整版)
2. [AI智能策略引擎规则说明（极简落地版）](#二-ai智能策略引擎规则说明-极简落地版)
3. [项目命名及规范](#三-项目命名及规范)
4. [案例存储格式说明](#四-成功失败案例存储格式说明)

# 一、API开发文档（智投引擎）完整版
**接口统一规范**
- 基础路径：`http://xxx.xxx.xxx.xxx:端口`
- 请求头：`Content-Type: application/json`
- 统一响应格式：
```json
{
  "code": 200,        // 200成功 500失败 401未授权 400参数错误 408接口超时
  "msg": "操作成功",  // 提示信息
  "data": {}          // 业务数据
}
```

---
## 第一部分：前端 ↔ Java后端 接口（运营平台核心）
### 1. 用户登录
- **请求方式**：POST
- **接口路径**：/api/user/login
- **入参**：
```json
{
  "username": "admin",
  "password": "123456"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userId": 1,
    "nickname": "运营管理员",
    "role": "admin"
  }
}
```

### 2. 自然语言投放指令下发
- **请求方式**：POST
- **接口路径**：/api/strategy/command
- **请求头**：token: {{token}}
- **入参**：
```json
{
  "command": "给25-35岁女性投放美妆广告，日预算5万，优先抖音",
  "userId": 1
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "指令已提交",
  "data": {
    "commandId": "CMD202603130001",
    "status": "待AI处理"
  }
}
```

### 3. 查询指令执行状态
- **请求方式**：GET
- **接口路径**：/api/strategy/command/status
- **请求头**：token: {{token}}
- **入参**：commandId=CMD202603130001
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "commandId": "CMD202603130001",
    "status": "待AI处理/处理中/已生成策略/待人工确认/执行失败/AI提问中",
    "strategyId": "STR202603130001",
    "failReason": "",
    "aiQuestion": "" // 新增：AI提问内容，状态为AI提问中时返回
  }
}
```

### 4. AI提问前端回复接口【新增】
- **请求方式**：POST
- **接口路径**：/api/strategy/command/reply
- **请求头**：token: {{token}}
- **入参**：
```json
{
  "commandId": "CMD202603130001",
  "replyContent": "日预算设置为8万元，投放渠道为抖音和小红书" // 前端补充的指令信息
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "回复已提交，AI将继续处理",
  "data": {
    "commandId": "CMD202603130001",
    "status": "处理中"
  }
}
```

### 5. AI策略预览/查询
- **请求方式**：GET
- **接口路径**：/api/strategy/info
- **请求头**：token: {{token}}
- **入参**：strategyId=STR202603130001
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "strategyId": "STR202603130001",
    "strategyName": "25-35岁女性美妆投放策略",
    "channels": ["抖音"],
    "budgetDay": 50000,
    "crowd": "25-35岁女性",
    "bidPrice": 0.8,
    "runTime": "08:00-23:00",
    "status": "待确认/待人工确认/投放中/已暂停", // 新增：待人工确认状态
    "createTime": "2026-03-13 12:00:00",
    "riskLevel": "普通/高风险" // 新增：风险等级，高风险为日预算≥10万
  }
}
```

### 6. 策略确认上线/手动编辑
- **请求方式**：POST
- **接口路径**：/api/strategy/confirm
- **请求头**：token: {{token}}
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "operateType": "上线/编辑",
  "editData": {
    "budgetDay": 60000,
    "bidPrice": 0.9
  }
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "策略已上线",
  "data": {
    "strategyId": "STR202603130001",
    "status": "投放中"
  }
}
```

### 7. 高风险策略人工确认【新增】
- **请求方式**：POST
- **接口路径**：/api/strategy/risk/confirm
- **请求头**：token: {{token}}
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "userId": 1,
  "confirmResult": "同意/拒绝" // 人工确认结果
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "高风险策略已确认",
  "data": {
    "strategyId": "STR202603130001",
    "status": "投放中/已拒绝",
    "confirmTime": "2026-03-13 14:00:00"
  }
}
```

### 8. 策略暂停/下线
- **请求方式**：POST
- **接口路径**：/api/strategy/stop
- **请求头**：token: {{token}}
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "operateType": "暂停/下线"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "strategyId": "STR202603130001",
    "status": "已暂停/已下线"
  }
}
```

### 9. 投放数据报表查询
- **请求方式**：GET
- **接口路径**：/api/report/adData
- **请求头**：token: {{token}}
- **入参**：strategyId=STR202603130001&startTime=2026-03-01&endTime=2026-03-13
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "strategyId": "STR202603130001",
    "expose": 120000,
    "click": 6500,
    "clickRate": 0.054,
    "convert": 320,
    "convertRate": 0.049,
    "cost": 48600,
    "roi": 3.2,
    "budgetDeviation": 0.028, // 新增：预算消耗偏差
    "dateList": [
      {"date":"2026-03-12","expose":12000,"click":650,"cost":4800,"roi":3.5}
    ]
  }
}
```

### 10. 策略列表分页查询
- **请求方式**：GET
- **接口路径**：/api/strategy/list
- **请求头**：token: {{token}}
- **入参**：pageNum=1&pageSize=10&status=投放中/待人工确认
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "total": 25,
    "pages": 3,
    "list": [
      {
        "strategyId": "STR202603130001",
        "strategyName": "25-35岁女性美妆投放策略",
        "channels": "抖音",
        "budgetDay": 50000,
        "status": "投放中/待人工确认",
        "riskLevel": "普通",
        "createTime": "2026-03-13 12:00:00"
      }
    ]
  }
}
```

### 11. 系统告警信息查询【新增】
- **请求方式**：GET
- **接口路径**：/api/notice/alert/list
- **请求头**：token: {{token}}
- **入参**：pageNum=1&pageSize=10
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "total": 5,
    "pages": 1,
    "list": [
      {
        "alertId": "ALT202603130001",
        "alertContent": "接口调用失败，策略STR202603130001暂未执行",
        "alertType": "接口异常",
        "relatedId": "STR202603130001", // 关联策略/指令ID
        "createTime": "2026-03-13 13:00:00",
        "status": "未读/已读"
      }
    ]
  }
}
```

---
## 第二部分：Python AI ↔ Java后端 接口（AI决策→执行）
### 1. AI获取投放指令列表
- **请求方式**：GET
- **接口路径**：/api/ai/command/list
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：status=待AI处理/AI提问中
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": [
    {
      "commandId": "CMD202603130001",
      "command": "给25-35岁女性投放美妆广告，日预算5万，优先抖音",
      "userId": 1
    }
  ]
}
```

### 2. AI更新指令处理状态
- **请求方式**：POST
- **接口路径**：/api/ai/command/update
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "commandId": "CMD202603130001",
  "status": "处理中/已完成/处理失败/AI提问中",
  "failReason": "",
  "aiQuestion": "" // 新增：AI提问内容，状态为AI提问中时必填
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "状态更新成功",
  "data": null
}
```

### 3. AI查询用户画像数据
- **请求方式**：GET
- **接口路径**：/api/ai/crowd/info
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：crowdTag=25-35岁女性
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "crowdId": "CR2026001",
    "crowdTag": "25-35岁女性",
    "userCount": 1250000,
    "preferTags": ["美妆","护肤","穿搭"],
    "activeTime": "08:00-23:00"
  }
}
```

### 4. AI查询历史投放效果数据
- **请求方式**：GET
- **接口路径**：/api/ai/report/history
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：crowdTag=25-35岁女性&channel=抖音
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "avgClickRate": 0.052,
    "avgConvertRate": 0.045,
    "avgBidPrice": 0.78,
    "suggestBid": 0.8,
    "suggestTime": "08:00-23:00"
  }
}
```

### 5. AI生成并同步策略到Java后端
- **请求方式**：POST
- **接口路径**：/api/ai/strategy/sync
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "commandId": "CMD202603130001",
  "strategyName": "25-35岁女性美妆投放策略",
  "channels": ["抖音"],
  "budgetDay": 50000,
  "crowdTag": "25-35岁女性",
  "bidPrice": 0.8,
  "runTime": "08:00-23:00",
  "productType": "美妆",
  "riskLevel": "普通/高风险" // 新增：AI标记的风险等级
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "策略同步成功",
  "data": {
    "strategyId": "STR202603130001",
    "status": "待确认/待人工确认" // 新增：根据风险等级自动赋值
  }
}
```

### 6. AI获取实时投放数据（用于策略优化）
- **请求方式**：GET
- **接口路径**：/api/ai/report/realTime
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：strategyId=STR202603130001
- **出参**：
```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "cost": 12500,
    "expose": 32000,
    "click": 1680,
    "convert": 82,
    "clickRate": 0.0525,
    "convertRate": 0.0488,
    "costRate": 0.25,
    "budgetDeviation": 0.025 // 新增：预算消耗偏差
  }
}
```

### 7. AI自动调整投放策略
- **请求方式**：POST
- **接口路径**：/api/ai/strategy/adjust
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "adjustType": "bidPrice/runTime/budgetDay",
  "oldValue": 0.8,
  "newValue": 0.85,
  "reason": "转化率高于预期，提高出价抢量"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "策略调整成功",
  "data": null
}
```

### 8. AI上报策略评估结果【新增】
- **请求方式**：POST
- **接口路径**：/api/ai/strategy/evaluate
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "commandId": "CMD202603130001",
  "evaluateResult": "成功/失败",
  "roi": 3.2,
  "budgetDeviation": 0.028,
  "evaluateReason": "ROI≥2，预算消耗偏差≤10%，判定为成功"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "评估结果上报成功",
  "data": {
    "caseId": "CASE202603130001"
  }
}
```

### 9. AI推送系统告警【新增】
- **请求方式**：POST
- **接口路径**：/api/ai/notice/alert/push
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "alertContent": "接口调用失败，策略STR202603130001暂未执行",
  "alertType": "接口异常/策略执行失败",
  "relatedId": "STR202603130001" // 关联策略/指令ID
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "告警推送成功",
  "data": {
    "alertId": "ALT202603130001"
  }
}
```

---
## 第三部分：Java后端 ↔ 广告渠道API 接口（投放执行）
### 1. 渠道广告创建
- **请求方式**：POST
- **接口路径**：/api/channel/ad/create
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "strategyId": "STR202603130001",
  "channel": "抖音",
  "adName": "25-35岁女性美妆广告",
  "budgetDay": 50000,
  "bidPrice": 0.8,
  "crowd": "25-35岁女性",
  "runTime": "08:00-23:00"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "广告创建成功",
  "data": {
    "adId": "AD_DOUYIN_10001",
    "status": "投放中"
  }
}
```

### 2. 渠道广告暂停/下线
- **请求方式**：POST
- **接口路径**：/api/channel/ad/operate
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "adId": "AD_DOUYIN_10001",
  "channel": "抖音",
  "operateType": "pause/stop"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "adId": "AD_DOUYIN_10001",
    "status": "已暂停/已下线"
  }
}
```

### 3. 渠道广告数据回传
- **请求方式**：POST
- **接口路径**：/api/channel/ad/report
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "adId": "AD_DOUYIN_10001",
  "channel": "抖音",
  "expose": 120000,
  "click": 6500,
  "convert": 320,
  "cost": 48600,
  "roi": 3.2 // 新增：ROI数据
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "数据同步成功",
  "data": null
}
```

---
## 第四部分：数据同步接口（ClickHouse ↔ Java后端）
### 1. 用户行为日志上报
- **请求方式**：POST
- **接口路径**：/api/data/log/report
- **请求头**：ai-token: sk_ai_ad_202603
- **入参**：
```json
{
  "userId": "10086",
  "eventType": "click/convert",
  "adId": "AD_DOUYIN_10001",
  "eventTime": "2026-03-13 12:30:00",
  "device": "手机",
  "city": "北京"
}
```
- **出参**：
```json
{
  "code": 200,
  "msg": "日志上报成功",
  "data": null
}
```

---
### 接口文档使用说明
1. **前端**：直接对接「第一部分」接口，完成登录、指令下发、AI提问回复、高风险确认、策略管理、数据报表、告警查看等开发
2. **Java后端**：实现全部接口，对接MySQL/ClickHouse、广告渠道API，完成鉴权校验、状态流转、告警存储
3. **Python AI**：对接「第二部分」接口，完成指令解析、AI提问、策略生成、风险标记、自我评估、告警推送、策略优化
4. 所有接口**入参、出参、请求方式固定**，异常返回按统一规范处理

# 二、AI智能策略引擎规则说明（极简落地版）
## 1. Token成本节省规则
### 1.1 模型分级调用（对接DeepSeek API：https://api.deepseek.com/v1，Key：sk-e88cf58b6b0648b287f782331cae6026）
- 简单指令（含**受众+渠道+日预算+产品类型**4个核心字段，无模糊表述）：调用DeepSeek轻量模型（deepseek-chat-lite）
- 复杂指令（缺失核心字段/多渠道多人群/模糊需求如“提升ROI”）：调用DeepSeek旗舰模型（deepseek-chat）
- 无模糊需求时，默认使用轻量模型

### 1.2 输入Token精简
- 指令解析阶段仅提取**受众、渠道、日预算、产品类型**核心字段，自动截断冗余描述（如“麻烦帮忙”“尽快处理”等无业务价值内容）
- 单次请求输入Token上限：1000 Token，超出则仅保留核心字段内容

### 1.3 缓存复用
- 通用解析结果缓存（如“25-35岁女性”“抖音美妆”等固定标签的解析结果），缓存有效期24小时
- 缓存命中时直接复用结果，无需重复调用DeepSeek API
- 缓存存储：本地内存缓存，核心键值对为「组合标签→解析结果」

## 2. 自然语言指令解析规则
### 2.1 核心字段校验
- 必检核心字段：**受众、渠道、日预算**（产品类型为可选，无则按渠道默认品类判定）
- 缺失任一必检字段，触发AI向前端提问流程

### 2.2 AI主动提问规则
- 提问触发：指令缺失核心必检字段
- 提问方式：调用`/api/ai/command/update`接口，将指令状态改为「AI提问中」，并传入具体提问内容
- 提问次数：仅1次，前端未在任意时间内回复，再次查询指令时直接返回「指令信息不全，无法生成策略」
- 回复处理：前端调用回复接口后，指令状态改为「处理中」，AI基于补充信息重新解析

## 3. 策略风险判定与人工二次确认规则
### 3.1 风险判定阈值
- 高风险策略唯一判定条件：**日预算 ≥ 10万元**
- 普通策略：日预算 ＜ 10万元，无需人工二次确认

### 3.2 人工确认流程
- AI生成高风险策略后，调用`/api/ai/strategy/sync`接口时标记`riskLevel: 高风险`，后端自动将策略状态设为「待人工确认」
- 前端在策略列表/详情页展示高风险标识，运营通过`/api/strategy/risk/confirm`接口完成确认
- 超时规则：人工2小时未确认，后端自动将策略状态改为「超时失效」，AI无需再处理
- 确认结果：同意则策略进入「待确认」可上线状态，拒绝则策略直接标记为「已拒绝」

## 4. Java接口调用重试/降级规则
### 4.1 重试规则
- 重试触发场景：接口返回500错误/408超时（超时阈值：3s）
- 重试次数：固定3次
- 重试间隔：指数退避，依次为1s → 2s → 4s
- 重试范围：Python AI调用的所有Java后端接口均适用

### 4.2 降级规则
- 降级触发：连续3次重试失败
- 降级动作：
  1. 调用`/api/ai/notice/alert/push`接口向前端推送告警信息，明确标注关联的策略/指令ID
  2. 终止当前策略生成/优化流程，调用对应接口将指令/策略状态改为「执行失败」，并填写失败原因为「接口调用失败，已触发降级」
  3. 本地记录失败日志，包含接口地址、调用时间、失败原因

## 5. 策略自我评估规则
### 5.1 评估触发时机
- 策略执行满24小时后，AI自动调用`/api/ai/report/realTime`获取最终投放数据，执行自我评估
- 评估完成后调用`/api/ai/strategy/evaluate`接口将评估结果上报至Java后端

### 5.2 成功/失败量化判定标准
| 判定结果 | 核心判定条件（需同时满足）| 预算消耗偏差计算公式       |
|----------|---------------------------------------|----------------------------|
| 成功     | 1. ROI ≥ 2；2. 预算消耗偏差 ≤ 10%      | 预算消耗偏差 = |实际消耗-预算| / 预算 |
| 失败     | 1. ROI ＜ 1；2. 预算消耗偏差 ＞ 20%    | 预算消耗偏差 = |实际消耗-预算| / 预算 |
| -        | 非上述两种情况，暂不标记成功/失败      | -                          |

### 5.3 评估结果应用
- 成功案例：核心参数（出价、时段、渠道配比）纳入RAG检索库，新策略生成时优先复用
- 失败案例：每日凌晨2点自动复盘，针对**出价（±0.1）、投放时段（±2小时）** 两个核心参数做优化调整

## 6. RAG落地规则（极简版，无向量库）
### 6.1 检索库存储
- 存储介质：本地文本文件（./rag/case.txt）+ JSON文件（./ai_evaluate/case.json）
- 存储内容：成功/失败案例的核心信息（人群、渠道、日预算、出价、时段、ROI、成败原因、评估结果）
- 新增规则：AI完成评估并上报后，实时将案例核心信息追加至上述两个文件

### 6.2 检索规则
- 检索触发：AI开始生成新策略时（解析完指令后，调用历史数据前）
- 检索关键词：**人群+渠道**（如“25-35岁女性+抖音”）
- 检索范围：近7天的成功/失败案例
- 结果限制：最多返回Top3匹配度最高的案例

### 6.3 检索结果融合规则
- 检索到成功案例：新策略直接复用其**出价、投放时段**核心参数，其余参数按历史投放数据生成
- 检索到失败案例：新策略避开其**出价、投放时段**参数（如失败案例出价0.9，则新策略出价≤0.8）
- 无匹配案例/无案例：按Java后端返回的历史投放数据生成默认策略
- 同时检索到成功+失败案例：优先遵循成功案例规则

## 7. 策略自动优化规则
### 7.1 优化触发时机
- 实时优化：策略投放中，每2小时获取一次实时数据，若出现异常则立即优化
- 复盘优化：每日凌晨2点，对前一日所有失败案例做参数优化

### 7.2 核心优化参数及规则
仅优化2个核心参数，其余参数暂不调整：
1. **出价（bidPrice）**：单次调整幅度±0.1，转化率低则下调，转化率高则上调
2. **投放时段（runTime）**：单次调整±2小时，根据用户活跃时间和转化高峰时段调整

### 7.3 优化验证
- 优化后的策略与原策略执行A/B测试，各分配50%日预算
- 12小时后对比两组ROI，保留效果更优的参数方案，自动同步至Java后端

# 三、项目命名及规范
## 1. 项目主命名（中文+英文，官方对外使用）
- **中文**：智投引擎
- **英文**：SmartAD Engine
- **缩写**：SmartAD（开发过程中文件/包名/变量名可使用）

## 2. 各模块命名规范（开发内部使用）
| 模块         | 中文命名       | 英文命名          | 缩写/包名规范       |
|--------------|----------------|-------------------|---------------------|
| 前端运营平台 | 智投引擎-运营端 | SmartAD-Admin     | smartad-admin       |
| Java后端核心 | 智投引擎-服务端 | SmartAD-Server    | smartad-server      |
| Python AI模块| 智投引擎-AI智能体 | SmartAD-Agent    | smartad-agent       |
| 数据存储层   | 智投引擎-数据层 | SmartAD-Data      | smartad-data        |

## 3. 命名使用规范
- 项目所有文档、代码包名、服务名称、配置文件均统一使用上述命名
- 数据库/表名/缓存键值对前缀统一使用：`smartad_`（如smartad_strategy、smartad_user）
- 接口路径、日志文件、告警标识均沿用上述命名规范，保证一致性

# 四、成功/失败案例存储格式说明
## 1. 本地JSON文件存储（./ai_evaluate/case.json）
### 1.1 存储结构（数组形式，新增案例向后追加）
```json
[
  {
    "caseId": "CASE202603130001",
    "strategyId": "STR202603130001",
    "commandId": "CMD202603130001",
    "crowdTag": "25-35岁女性",
    "channels": ["抖音"],
    "budgetDay": 50000,
    "bidPrice": 0.8,
    "runTime": "08:00-23:00",
    "productType": "美妆",
    "roi": 3.2,
    "budgetDeviation": 0.028,
    "evaluateResult": "成功",
    "evaluateReason": "ROI≥2，预算消耗偏差≤10%，判定为成功",
    "evaluateTime": "2026-03-14 12:00:00",
    "createTime": "2026-03-13 12:00:00"
  }
]
```
### 1.2 字段说明
| 字段            | 类型        | 说明                     |
|-----------------|-------------|--------------------------|
| caseId          | String      | 案例ID，格式：CASE+时间戳+序号 |
| strategyId      | String      | 关联策略ID               |
| commandId       | String      | 关联指令ID               |
| crowdTag        | String      | 投放人群标签             |
| channels        | Array       | 投放渠道数组             |
| budgetDay       | Number      | 日预算（元）|
| bidPrice        | Number      | 出价                     |
| runTime         | String      | 投放时段                 |
| productType     | String      | 产品类型                 |
| roi             | Number      | 实际ROI值                |
| budgetDeviation | Number      | 预算消耗偏差             |
| evaluateResult  | String      | 评估结果：成功/失败      |
| evaluateReason  | String      | 评估判定原因             |
| evaluateTime    | String      | 评估完成时间             |
| createTime      | String      | 策略创建时间             |

### 1.3 归档规则
- 每日凌晨3点自动归档前一日的案例数据
- 归档文件命名：case_20260313.json（按日期命名）
- 归档路径：./ai_evaluate/archive/

## 2. RAG检索文本文件（./rag/case.txt）
### 2.1 存储格式（每行一个案例，按「人群+渠道+核心信息+成败原因」整理）
```
CASE202603130001|25-35岁女性+抖音|日预算50000|出价0.8|时段08:00-23:00|ROI3.2|预算偏差2.8%|成功|原因：ROI≥2，预算消耗偏差≤10%
CASE202603130002|18-25岁男性+快手|日预算80000|出价0.5|时段18:00-24:00|ROI0.8|预算偏差25%|失败|原因：ROI＜1，预算消耗偏差＞20%
```
### 2.2 分隔符说明
- 字段之间用`|`分隔，固定顺序不可调整
- 人群+渠道用`+`连接，作为核心检索关键词
- 数值类字段直接填写具体值，百分比保留1位小数

### 2.3 检索匹配规则
- 按「人群+渠道」模糊匹配，如检索“25-35岁女性+抖音”，匹配包含该字符的行
- 优先匹配完全一致的关键词，再匹配模糊关键词
- 最多返回Top3匹配结果，按评估时间倒序排列