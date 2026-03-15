"""
评估结果本地存档（可选）：将每次 AI 评估结果保存为 JSON 文件，便于离线分析。
"""
import json
import os
from datetime import datetime
from loguru import logger

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)


def save_evaluate_result(strategy_id: str, result: dict) -> None:
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{date_str}_{strategy_id}.json"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "strategyId": strategy_id,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }, f, ensure_ascii=False, indent=2)
        logger.debug(f"评估结果已存档: {filepath}")
    except Exception as e:
        logger.warning(f"评估结果存档失败: {e}")
