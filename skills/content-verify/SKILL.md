---
name: content-verify
description: 交叉验证新闻、科普和自媒体内容的可信度，识别虚假信息和伪科学。当用户需要：1) 验证某条新闻或传言的真假；2) 检验科学/健康声称是否有科学依据；3) 识别伪科学标志（量子医疗、包治百病等）；4) 对内容进行可信度评分（0-100）时使用此 skill。
metadata: {"openclaw": {"requires": {"bins": ["uv"], "env": ["SERPAPI_API_KEY"]}, "primaryEnv": "SERPAPI_API_KEY"}}
---

# Content Verify Skill

通过 SerpAPI 网络检索，对新闻、科普和自媒体内容进行交叉验证并给出可信度评分。

## 配置

脚本需要 SerpAPI API Key（[serpapi.com](https://serpapi.com) 免费套餐每月 100 次）。

**方式 A — OpenClaw env 注入（推荐）：**
在 `~/.openclaw/.env` 中设置：
```
SERPAPI_API_KEY=your-key-here
```

**方式 B — skill 本地 .env：**
```bash
cp scripts/.env.example scripts/.env
# 编辑 scripts/.env，填入真实值
```

**方式 C — CLI 直接传入：**
```bash
uv run scripts/search.py --api-key your-key "搜索词"
```

可选参数（均有默认值）：
- `SERPAPI_LOCATION` — 搜索地区（默认 `Austin, Texas, United States`）
- `SERPAPI_HL` — 搜索语言（默认 `zh-cn`）
- `SERPAPI_GL` — 搜索国家（默认 `cn`）

## 脚本位置

```bash
# 安装后
uv run ~/.openclaw/skills/content-verify/scripts/search.py "<搜索词>"

# 项目内使用
uv run ./skills/content-verify/scripts/search.py "<搜索词>"
```

## 使用方法

### 网络搜索（证据收集）

```bash
uv run scripts/search.py "<搜索关键词>"
uv run scripts/search.py "<搜索关键词>" --num 5
uv run scripts/search.py "<搜索关键词>" --format json
```

### 验证流程（由 AI 主导）

**通用内容验证：**
1. 提取核心声称和关键实体
2. 执行搜索：`uv run scripts/search.py "<实体+事件关键词>"`
3. 交叉核查多个来源的一致性
4. 识别风险因素（来源缺失、情感化语言、孤证等）
5. 输出 0-100 可信度评分和等级

**新闻验证：**
1. 搜索新闻中的具体声称
2. 检查其他权威媒体是否有同样报道
3. 分析时间线一致性
4. 评估信息来源权威性
5. 给出评分：VERIFIED(90-100) / HIGH(75-89) / MEDIUM(50-74) / LOW(25-49) / FALSE(0-24)

**科学主张验证（自动预检伪科学）：**
1. 扫描伪科学标志：
   - 🚨 "量子" + 医学词（量子水疗、量子能量治疗）
   - 🚨 "包治百病" / "万能药" / "没有副作用"
   - 🚨 "医学界隐瞒" / "科学家不敢说"
   - 🚨 "祖传秘方" / "排毒产品"
2. 搜索权威科学机构和同行评审来源
3. 评估证据等级（一级A/B → 二级 → 三级 → 无证据 → 反证据）
4. 核查专家共识

## 示例

### 验证新闻传言
```
用户：hunter alpha 是之前 openrouter 的匿名模型，后来传出是 deepseek v4，也有说是 Xiaomi MiMo-V2-Pro

AI 操作：
uv run scripts/search.py "hunter alpha openrouter anonymous model identity"
uv run scripts/search.py "hunter alpha deepseek v4 openclaw"
uv run scripts/search.py "Xiaomi MiMo-V2-Pro openrouter"
→ 综合搜索结果给出可信度评分
```

### 检验科学声称
```
用户：量子水疗能治愈慢性病

AI 操作：
⚠️ 伪科学预检：检测到"量子+医学词"标志
uv run scripts/search.py "量子水疗 科学研究 证据"
uv run scripts/search.py "quantum water therapy scientific evidence"
→ 评分 0-24（FALSE），标注反证据
```

### 验证健康建议
```
用户：维生素C大剂量服用能预防感冒

AI 操作：
uv run scripts/search.py "vitamin C high dose cold prevention clinical trial"
uv run scripts/search.py "大剂量维生素C 预防感冒 研究"
→ 根据随机对照试验证据评分
```

## 评分标准

| 评分 | 等级 | 说明 |
|------|------|------|
| 90-100 | ✅ VERIFIED | 已被多个权威来源独立验证 |
| 75-89  | 🟢 HIGH | 来源可信，事实基本准确 |
| 50-74  | 🟡 MEDIUM | 有限证据或部分有争议 |
| 25-49  | 🟠 LOW | 缺乏权威来源支持 |
| 0-24   | 🔴 FALSE | 明显虚假或已知伪科学 |

## 重要提示

- **未经网络检索不得直接给出高置信度结论**
- 若检索证据不足，明确标注"证据不足/待进一步核实"
- 搜索结果仅作为证据候选，不等于事实结论
- 对争议内容建议多关键词、多角度搜索
