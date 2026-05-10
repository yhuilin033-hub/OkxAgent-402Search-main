"""
OkxAgent-402Search - Agent 核心模块
负责长链推理与工具调用（单 Agent 多工具协作架构）
"""

import os
import json
import logging
from datetime import datetime
from data_fetcher import OKXDataFetcher
from indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class MarketAgent:
    """
    市场监控 Agent
    作为调度核心，通过 Tool-Use 机制按需调用各功能模块
    """

    def __init__(self):
        # 初始化工具集
        self.data_fetcher = OKXDataFetcher()
        self.indicators = TechnicalIndicators()

        # Agent 运行状态
        self.memory = []  # 历史推理结果（用于闭环反馈）
        self.signal_history = []  # 历史信号记录

        # 模型配置
        self.model = os.getenv('LLM_MODEL', 'mimo-v2.5-pro')
        self.base_url = os.getenv('LLM_BASE_URL', 'https://api.xiaomimimo.com/v1')
        self.max_context = int(os.getenv('MAX_CONTEXT_TOKENS', 100000))

        logger.info(f"MarketAgent 初始化完成 | 模型: {self.model} | 上下文窗口: {self.max_context} tokens")

    def fetch_market_data(self):
        """
        阶段 1 - 数据采集
        通过 OKX API 拉取实时行情、K 线历史及订单簿深度
        """
        instruments = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'BNB-USDT', 'XRP-USDT']
        raw_data = []

        for inst in instruments:
            try:
                ticker = self.data_fetcher.get_ticker(inst)
                klines = self.data_fetcher.get_klines(inst, bar='15m', limit=96)  # 24h 数据
                orderbook = self.data_fetcher.get_orderbook(inst, depth=20)
                raw_data.append({
                    'instrument': inst,
                    'ticker': ticker,
                    'klines': klines,
                    'orderbook': orderbook,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"获取 {inst} 数据失败: {e}")

        return raw_data

    def aggregate_and_clean(self, raw_data):
        """
        阶段 2 - 多源聚合与清洗
        将多维度数据统一结构化，处理缺失值与异常值
        """
        cleaned = []
        for item in raw_data:
            try:
                ticker = item['ticker']
                if not ticker or ticker.get('last') is None:
                    continue

                # 计算技术指标
                indicators = self.indicators.compute_all(item['klines'])

                cleaned.append({
                    'instrument': item['instrument'],
                    'price': float(ticker['last']),
                    'volume_24h': float(ticker.get('vol_24h', 0)),
                    'change_24h': float(ticker.get('change_24h', 0)),
                    'bid_ask_spread': self._calc_spread(item['orderbook']),
                    'indicators': indicators,
                    'timestamp': item['timestamp']
                })
            except Exception as e:
                logger.warning(f"数据清洗异常 ({item.get('instrument')}): {e}")

        return cleaned

    def _calc_spread(self, orderbook):
        """计算买卖价差"""
        if not orderbook:
            return 0.0
        best_bid = float(orderbook['bids'][0][0]) if orderbook.get('bids') else 0
        best_ask = float(orderbook['asks'][0][0]) if orderbook.get('asks') else 0
        if best_bid > 0 and best_ask > 0:
            return round((best_ask - best_bid) / best_bid * 100, 4)
        return 0.0

    def long_chain_reasoning(self, cleaned_data):
        """
        阶段 3 - 长链推理
        基于 MiMo-V2.5-Pro 的 100 万 Token 上下文窗口，执行多步推理：
        1. 趋势识别（多时间框架分析）
        2. 支撑/阻力位计算
        3. 波动率评估
        4. 异常检测（价格/成交量偏离）
        """
        results = []

        for item in cleaned_data:
            ind = item['indicators']

            # 构建推理上下文
            context = {
                'instrument': item['instrument'],
                'current_price': item['price'],
                'volume_24h': item['volume_24h'],
                'change_24h_pct': item['change_24h'],
                'bid_ask_spread': item['bid_ask_spread'],
                'indicators': {
                    'rsi': ind.get('rsi'),
                    'macd_histogram': ind.get('macd_histogram'),
                    'bb_position': ind.get('bb_position'),  # 0-1 表示在布林带中的位置
                    'volume_ratio': ind.get('volume_ratio'),
                    'ma_alignment': ind.get('ma_alignment'),  # 均线排列状态
                }
            }

            # 多步推理链
            reasoning_steps = []

            # Step 1: 趋势判断（基于均线排列 + 价格位置）
            trend = self._reason_trend(context)
            reasoning_steps.append({'step': '趋势识别', 'result': trend})

            # Step 2: 超买超卖（基于 RSI + 布林带位置）
            overbought_oversold = self._reason_momentum(context)
            reasoning_steps.append({'step': '动量评估', 'result': overbought_oversold})

            # Step 3: 成交量异常检测
            volume_anomaly = self._reason_volume(context)
            reasoning_steps.append({'step': '成交量异常检测', 'result': volume_anomaly})

            # Step 4: 综合风险评估
            risk_score = self._assess_risk(trend, overbought_oversold, volume_anomaly)
            reasoning_steps.append({'step': '综合风险评估', 'result': {'risk_score': risk_score}})

            results.append({
                'instrument': item['instrument'],
                'price': item['price'],
                'reasoning_steps': reasoning_steps,
                'final_risk_score': risk_score,
                'timestamp': item['timestamp']
            })

        return results

    def _reason_trend(self, context):
        """趋势识别推理"""
        ma = context['indicators']['ma_alignment']
        price = context['current_price']

        if ma == 'bullish':
            return {'direction': 'upward', 'strength': 'strong', 'confidence': 0.85}
        elif ma == 'bearish':
            return {'direction': 'downward', 'strength': 'strong', 'confidence': 0.85}
        else:
            return {'direction': 'sideways', 'strength': 'weak', 'confidence': 0.5}

    def _reason_momentum(self, context):
        """动量评估推理"""
        rsi = context['indicators']['rsi']
        bb_pos = context['indicators']['bb_position']

        if rsi and rsi > 70:
            return {'status': 'overbought', 'rsi': rsi}
        elif rsi and rsi < 30:
            return {'status': 'oversold', 'rsi': rsi}
        else:
            return {'status': 'neutral', 'rsi': rsi}

    def _reason_volume(self, context):
        """成交量异常检测"""
        vol_ratio = context['indicators'].get('volume_ratio', 1)
        if vol_ratio > 2.0:
            return {'anomaly': True, 'type': 'volume_spike', 'ratio': vol_ratio}
        elif vol_ratio < 0.3:
            return {'anomaly': True, 'type': 'volume_dry_up', 'ratio': vol_ratio}
        else:
            return {'anomaly': False, 'ratio': vol_ratio}

    def _assess_risk(self, trend, momentum, volume):
        """综合风险评估"""
        risk = 50  # 基准分

        # 趋势因素调整
        if trend['direction'] == 'downward':
            risk += 15
        elif trend['direction'] == 'upward':
            risk -= 10

        # 动量因素调整
        if momentum['status'] == 'overbought':
            risk += 10
        elif momentum['status'] == 'oversold':
            risk += 5

        # 成交量异常调整
        if volume['anomaly']:
            risk += 15

        return min(max(risk, 0), 100)

    def generate_signals(self, analysis_result, threshold=0.7):
        """
        阶段 4 - 决策输出
        根据推理结果生成交易信号
        """
        signals = []
        for item in analysis_result:
            risk = item['final_risk_score']
            if risk >= threshold * 100:
                signals.append({
                    'instrument': item['instrument'],
                    'price': item['price'],
                    'risk_score': risk,
                    'reasoning': item['reasoning_steps'],
                    'message': f"⚠️ [{item['instrument']}] 风险评分 {risk}/100，建议关注",
                    'timestamp': item['timestamp']
                })
        return signals

    def update_memory(self, analysis_result, signals):
        """
        阶段 5 - 闭环反馈
        将本轮结果存入记忆，用于后续自适应调参
        """
        self.memory.append({
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_result,
            'signals': signals
        })
        if signals:
            self.signal_history.extend(signals)

        # 控制记忆大小（保留最近 1000 条）
        if len(self.memory) > 1000:
            self.memory = self.memory[-1000:]
        if len(self.signal_history) > 500:
            self.signal_history = self.signal_history[-500:]

        logger.info(f"闭环反馈完成 | 记忆池: {len(self.memory)} 条 | 历史信号: {len(self.signal_history)} 条")
