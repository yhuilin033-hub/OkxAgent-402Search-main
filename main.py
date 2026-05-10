"""
OkxAgent-402Search - 主入口
基于 AI 驱动的 OKX 加密货币市场监控与智能预警 Agent
"""

import os
import time
import logging
from dotenv import load_dotenv
from agent import MarketAgent
from notifier import Notifier

# 加载环境变量
load_dotenv()

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("OkxAgent-402Search 启动中...")
    logger.info("核心逻辑流：数据采集 → 多源聚合 → 长链推理 → 决策输出 → 闭环反馈")
    logger.info("=" * 60)

    # 初始化组件
    agent = MarketAgent()
    notifier = Notifier()

    # 获取运行参数
    poll_interval = int(os.getenv('POLL_INTERVAL_SECONDS', 60))
    signal_threshold = float(os.getenv('SIGNAL_THRESHOLD', 0.7))

    logger.info(f"轮询间隔: {poll_interval}s | 信号阈值: {signal_threshold}")
    logger.info("Agent 开始持续监控市场...")

    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            logger.info(f"--- 第 {cycle_count} 轮监控循环开始 ---")

            # 阶段 1：数据采集
            raw_data = agent.fetch_market_data()
            logger.info(f"[阶段1] 数据采集完成，获取 {len(raw_data)} 条行情记录")

            # 阶段 2：多源聚合与清洗
            cleaned_data = agent.aggregate_and_clean(raw_data)
            logger.info(f"[阶段2] 数据聚合完成，有效数据 {len(cleaned_data)} 条")

            # 阶段 3：长链推理
            analysis_result = agent.long_chain_reasoning(cleaned_data)
            logger.info(f"[阶段3] 长链推理完成")

            # 阶段 4：决策输出
            signals = agent.generate_signals(analysis_result, threshold=signal_threshold)
            if signals:
                logger.info(f"[阶段4] 生成 {len(signals)} 条交易信号")
                for signal in signals:
                    notifier.send_alert(signal)
            else:
                logger.info("[阶段4] 当前无满足阈值的交易信号")

            # 阶段 5：闭环反馈（将本轮结果存入记忆，用于后续自适应调参）
            agent.update_memory(analysis_result, signals)

            logger.info(f"--- 第 {cycle_count} 轮监控循环完成 ---\n")

        except KeyboardInterrupt:
            logger.info("收到中断信号，Agent 正在安全退出...")
            break
        except Exception as e:
            logger.error(f"监控循环异常: {e}", exc_info=True)

        time.sleep(poll_interval)

    logger.info("OkxAgent-402Search 已停止。")


if __name__ == '__main__':
    main()
