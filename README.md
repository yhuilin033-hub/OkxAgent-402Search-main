# OkxAgent-402Search

基于 AI 驱动的 OKX 加密货币市场监控与智能预警 Agent，专为 MiMo Orbit Token 激励计划构建。

## 核心功能

- **自动化行情采集**：定时拉取 OKX 现货/合约实时价格与 K 线数据
- **多源数据聚合**：清洗、去重并结构化存储多维度市场数据
- **长链推理引擎**：基于大模型对历史序列数据进行趋势识别、支撑/阻力位计算与异常检测
- **智能预警推送**：交易信号生成后通过 Webhook 实时推送至 Telegram/钉钉
- **闭环反馈优化**：根据用户反馈与实盘结果自动调整信号阈值

## 核心逻辑流

```
数据采集 → 多源聚合 → 长链推理 → 决策输出 → 闭环反馈
（OKX API） （清洗去重） （MiMo-V2.5-Pro 推理） （微信/钉钉推送） （自适应调参）
```

## 技术栈

- **Agent 框架**：OpenClaw
- **底层模型**：MiMo-V2.5-Pro / Claude / DeepSeek
- **语言**：Python 3.10+
- **数据源**：OKX REST API / WebSocket
- **推送通道**：Telegram Bot / 钉钉 Webhook

## 快速开始

1. 克隆仓库

```bash
git clone https://github.com/yhuilin033-hub/OkxAgent-402Search-main.git
cd OkxAgent-402Search-main
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 OKX API Key、大模型 API Key、通知 Webhook 地址等
```

4. 运行 Agent

```bash
python main.py
```

## 项目结构

```
├── main.py              # Agent 主调度入口
├── agent.py             # Agent 核心逻辑（长链推理与工具调用）
├── data_fetcher.py      # OKX API 数据采集模块
├── indicators.py        # 技术指标计算模块
├── notifier.py          # 消息推送模块
├── config.py            # 配置管理
├── requirements.txt     # Python 依赖
└── .env.example         # 环境变量模板
```

## Token 消耗

- 日均 API 请求：约 400 次
- 日均 Token 消耗：约 2000 万
- 支持模型：MiMo-V2.5-Pro、Claude 系列、DeepSeek 系列等

## License

MIT License
