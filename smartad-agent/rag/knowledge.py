"""
RAG 知识库模块
- CROWD_KNOWLEDGE / CHANNEL_KNOWLEDGE / STRATEGY_RULES: 原始知识文本（兼容）
- CROWD_DATABASE / CHANNEL_DATABASE: 结构化数据（供向量种子导入）
- 新增知识可通过 KnowledgeRetriever 动态添加到向量库
"""

# ──────────────────────────────────────────────────────────────────────────────
# 结构化数据库（供向量种子导入 & 关键词检索降级）
# ──────────────────────────────────────────────────────────────────────────────

CROWD_DATABASE = [
    {
        "tag": "young_fashion",
        "description": "18-28岁时尚女性，对服饰、美妆敏感，转化率高但客单价中等",
        "avg_order_value": "中等",
        "conversion_rate": "高",
        "bid_strategy": "中等出价，竞争激烈",
    },
    {
        "tag": "middle_income",
        "description": "30-45岁中等收入家庭，偏向品质消费，客单价高，转化周期稍长",
        "avg_order_value": "高",
        "conversion_rate": "中等",
        "bid_strategy": "高出价，精准定向",
    },
    {
        "tag": "senior_tech",
        "description": "45岁以上科技爱好者，忠诚度高，ROI稳定",
        "avg_order_value": "高",
        "conversion_rate": "稳定",
        "bid_strategy": "稳定出价，长尾投放",
    },
    {
        "tag": "student",
        "description": "18-25岁在校学生，价格敏感，活跃度高",
        "avg_order_value": "低",
        "conversion_rate": "高",
        "bid_strategy": "低出价，冲量为主",
    },
    {
        "tag": "enterprise",
        "description": "B端企业采购决策人，转化率低但客单价极高",
        "avg_order_value": "极高",
        "conversion_rate": "低",
        "bid_strategy": "高出价，精准触达",
    },
]

CHANNEL_DATABASE = [
    {
        "channel": "douyin",
        "feature": "短视频平台，曝光量大，适合品牌曝光和冲量；出价竞争激烈",
        "best_for": "品牌曝光、新品上市、冲量",
        "bid_range": "中等偏高",
        "audience": "全年龄段，年轻化",
    },
    {
        "channel": "kuaishou",
        "feature": "下沉市场用户为主，转化率较高，单价适中",
        "best_for": "下沉市场、电商导购",
        "bid_range": "中等",
        "audience": "下沉市场，30+为主",
    },
    {
        "channel": "weibo",
        "feature": "兴趣图谱精准，适合中高端品牌，曝光较贵",
        "best_for": "品牌形象、明星同款、社会热点",
        "bid_range": "高",
        "audience": "一二线城市，白领",
    },
    {
        "channel": "toutiao",
        "feature": "算法分发精准，适合信息流广告，中等出价可覆盖广泛用户",
        "best_for": "信息流广告、效果广告",
        "bid_range": "中等",
        "audience": "全年龄段",
    },
    {
        "channel": "baidu",
        "feature": "搜索意图明确，转化率最高，但流量成本高",
        "best_for": "搜索拦截、高意图用户",
        "bid_range": "高",
        "audience": "主动搜索用户",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# 原始知识文本（保持向后兼容，供 Prompt 直接注入和降级使用）
# ──────────────────────────────────────────────────────────────────────────────

CROWD_KNOWLEDGE = """\
## 人群画像说明
| 人群标签       | 描述                                      |
|--------------|------------------------------------------|
| young_fashion | 18-28岁时尚女性，对服饰、美妆敏感，转化率高但客单价中等 |
| middle_income | 30-45岁中等收入家庭，偏向品质消费，客单价高，转化周期稍长 |
| senior_tech   | 45岁以上科技爱好者，忠诚度高，ROI稳定             |
| student       | 18-25岁在校学生，价格敏感，活跃度高               |
| enterprise    | B端企业采购决策人，转化率低但客单价极高             |
"""

CHANNEL_KNOWLEDGE = """\
## 渠道特征说明
| 渠道     | 特征                                      |
|---------|------------------------------------------|
| douyin  | 短视频平台，曝光量大，适合品牌曝光和冲量；出价竞争激烈   |
| kuaishou| 下沉市场用户为主，转化率较高，单价适中              |
| weibo   | 兴趣图谱精准，适合中高端品牌，曝光较贵               |
| toutiao | 算法分发精准，适合信息流广告，中等出价可覆盖广泛用户     |
| baidu   | 搜索意图明确，转化率最高，但流量成本高               |
"""

STRATEGY_RULES = """\
## 投放策略规则
1. 日预算不得低于 ¥100，不得高于 ¥100,000
2. 出价（bidPrice）单位为分，取值范围 [10, 10000] 分
3. 高风险策略：单条策略日预算超过 ¥5000 或出价超过 ¥50（5000分），需人工确认
4. 同一人群+渠道组合，同一时间只能有一条投放中策略
5. CTR < 0.5% 或 ROI < 1.0 时应触发调整建议
"""
