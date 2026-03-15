agent测试结果

```
d:\开发经验总结\java\资料\我可以看\SmartAD-Engine\smartad-agent>E:\develop\python311\python.exe test_agent.py T2 T3 T4 T5 T6 T7

仅运行测试: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7']

═══════════════════════════════════════════════════════

  SmartAD Agent — 功能验证测试

═══════════════════════════════════════════════════════

───────────────────────────────────────────────────────

 T2. LLM 连通性测试

───────────────────────────────────────────────────────

  [>>] 轻量模型 响应: '1' (1858ms)

  OK T2.轻量模型连通 — 1858ms

  [>>] 标准模型 响应: '1' (1234ms)

  OK T2.标准模型连通 — 1234ms

───────────────────────────────────────────────────────

 T3. 路由链（意图分类）

───────────────────────────────────────────────────────

  [>>] 指令: 「给18-25岁学生投放电商广告，日预算500元，抖音渠道...」→ simple (指令明确指定了目标人群（18-25岁学生）、渠道（抖音）、预)

  OK T3.路由[simple] — simple

  [>>] 指令: 「帮我做个广告...」→ complex (指令过于模糊，未指定广告目标、受众、渠道、预算等关键信息)

  OK T3.路由[complex] — complex

  [>>] 指令: 「帮我写一首诗...」→ invalid (指令与广告投放无关，属于诗歌创作请求)

  OK T3.路由[invalid] — invalid

───────────────────────────────────────────────────────

 T4. 指令解析链（含反思）

───────────────────────────────────────────────────────

2026-03-15 13:27:43.620 | DEBUG    | chains.command_chain:run_parse_with_reflection:93 - [ParseChain] 初始草案: {'strategies': [{'crowdId': 1, 'crowdTag': 'young_fashion', 'channel': 'douyin', 'budgetDay': 1000, 'bidPrice': 120, 'reason': '人群画像匹配（18-28岁时尚女性），抖音渠道曝光量大适合美妆品牌曝光，出价参考历史建议出价，预算在安全范围内。'}], 'hasQuestion': False, 'question': ''}

2026-03-15 13:28:26.682 | DEBUG    | chains.command_chain:run_parse_with_reflection:111 - [ReflectChain] 第1次反思完成

  [>>] 指令: 「给年轻女性投放美妆广告，日预算1000元，抖音渠道」

  [>>] 耗时: 49196ms

  [>>]   策略: young_fashion × douyin 预算=1000元 出价=120分

  [>>]   理由: 人群画像匹配（18-28岁时尚女性），抖音渠道曝光量大适合美妆品牌曝光，出价参考历史建议出价，预算在安全范围内。

  OK T4.解析[策略生成] — 1条策略

2026-03-15 13:28:41.461 | DEBUG    | chains.command_chain:run_parse_with_reflection:93 - [ParseChain] 初始草案: {'strategies': [{'crowdId': 1, 'crowdTag': 'young_fashion', 'channel': 'douyin', 'budgetDay': 1000, 'bidPrice': 120, 'reason': '抖音平台适合年轻时尚女性进行品牌曝光与转化，历史数据建议出价，分配一半预算以平衡渠道。'}, {'crowdId': 3, 'crowdTag': 'middle_income', 'channel': 'douyin', 'budgetDay': 500, 'bidPrice': 150, 'reason': '抖音兴趣图谱有助于触达追求品质的中等收入人群，略高出价以在竞争环境中获取优质流量。'}, {'crowdId': 1, 'crowdTag': 'young_fashion', 'channel': 'kuaishou', 'budgetDay': 300, 'bidPrice': 100, 'reason': '快手下沉市场转化率较高，适合年轻人群，采用更具性价比的出价以优化成本。'}, {'crowdId': 3, 'crowdTag': 'middle_income', 'channel': 'kuaishou', 'budgetDay': 200, 'bidPrice': 130, 'reason': '快手平台同样覆盖广泛家庭用户，以适中出价尝试触达中等收入人群，作为抖音渠道的补充。'}], 'hasQuestion': False, 'question': ''}

2026-03-15 13:29:23.238 | DEBUG    | chains.command_chain:run_parse_with_reflection:111 - [ReflectChain] 第1次反思完成

  [>>] 指令: 「在抖音和快手同时投放，覆盖年轻人和中等收入人群，每天预算2000」

  [>>] 耗时: 56552ms

  [>>]   策略: young_fashion × douyin 预算=1000元 出价=120分

  [>>]   理由: 抖音平台适合年轻时尚女性进行品牌曝光与转化，历史数据建议出价，分配一半预算以平衡渠道。

  [>>]   策略: middle_income × douyin 预算=500元 出价=150分

  [>>]   理由: 抖音兴趣图谱有助于触达追求品质的中等收入人群，略高出价以在竞争环境中获取优质流量。

  [>>]   策略: young_fashion × kuaishou 预算=300元 出价=100分

  [>>]   理由: 快手下沉市场转化率较高，适合年轻人群，采用更具性价比的出价以优化成本。

  [>>]   策略: middle_income × kuaishou 预算=200元 出价=130分

  [>>]   理由: 快手平台同样覆盖广泛家庭用户，以适中出价尝试触达中等收入人群，作为抖音渠道的补充。

  OK T4.解析[策略生成] — 4条策略

───────────────────────────────────────────────────────

 T5. 追问回答链

───────────────────────────────────────────────────────

2026-03-15 13:29:29.340 | DEBUG    | chains.command_chain:run_parse_with_reflection:93 - [ParseChain] 初始草案: {'strategies': [{'crowdId': 1, 'crowdTag': 'young_fashion', 'channel': 'douyin', 'budgetDay': 800, 'bidPrice': 150, 'reason': '抖音平台曝光量大，适合时尚年轻女性进行品牌曝光和冲量。初始出价设为150分（1.5元）以在竞争环境中获取较好展示位置。日预算800元符合平台规则，且未触发高风险阈值。'}], 'hasQuestion': False, 'question': ''}

2026-03-15 13:30:20.258 | DEBUG    | chains.command_chain:run_parse_with_reflection:111 - [ReflectChain] 第1次反思完成

  [>>] 追问后策略: young_fashion × douyin

  OK T5.追问回答 — 1条策略

───────────────────────────────────────────────────────

 T6. 策略评估链

───────────────────────────────────────────────────────

  [>>] 耗时: 6329ms

  [>>] needAdjust: True

  [>>] adjustType: bid_up

  [>>] roi: 1.83  budgetDeviation: 0.0

  [>>] score: 72

  [>>] reason: CTR（0.016）低于0.5%的预警线，但ROI（1.83）表现良好。建议小幅提升出价以争抢更多优质流量，尝试提升CT

  OK T6.评估链 — score=72

───────────────────────────────────────────────────────

 T7. 告警链

───────────────────────────────────────────────────────

  [>>] 耗时: 3186ms

  [>>] hasAlert: True

  [>>] alertType: low_roi

  [>>] alertLevel: warning

  [>>] alertMessage: 过去3天ROI持续低于1.0，建议暂停或降低出价

  OK T7.告警链 — hasAlert=True

═══════════════════════════════════════════════════════

  测试结果汇总

═══════════════════════════════════════════════════════

  [PASS] T2.轻量模型连通 — 1858ms

  [PASS] T2.标准模型连通 — 1234ms

  [PASS] T3.路由[simple] — simple

  [PASS] T3.路由[complex] — complex

  [PASS] T3.路由[invalid] — invalid

  [PASS] T4.解析[策略生成] — 1条策略

  [PASS] T4.解析[策略生成] — 4条策略

  [PASS] T5.追问回答 — 1条策略

  [PASS] T6.评估链 — score=72

  [PASS] T7.告警链 — hasAlert=True

  总计: 10 项 | 通过: 10 | 失败: 0

```

