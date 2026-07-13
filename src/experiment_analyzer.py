import pandas as pd
import numpy as np

COMPARISON_METRICS = (
    "exposure_rate",
    "attempt_rate_given_exposed",
    "payment_rate_given_attempt",
    "overall_payment_rate",
    "refund_rate_given_paid",
    "arpu",
    "net_arpu",
    "avg_payment_latency_ms",
)

def compare_group_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """
    比较实验组指标，返回一个包含比较结果的 DataFrame。
    """
    if "A" not in metrics.index or "B" not in metrics.index:
        raise ValueError("实验组 A 或 B 的指标缺失，无法进行比较。")

    comparison = pd.DataFrame(
        {
            "A": metrics.loc["A", list(COMPARISON_METRICS)],
            "B": metrics.loc["B", list(COMPARISON_METRICS)],
        }
    )

    comparison["absolute_change"] = (
        comparison["B"] - comparison["A"]
    )

    comparison["relative_uplift"] = (
        comparison["absolute_change"]
        / comparison["A"].replace(0, np.nan)
    )

    return comparison