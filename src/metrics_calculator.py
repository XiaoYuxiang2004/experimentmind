from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    安全计算比率；当分母为 0 时返回 NaN。
    """
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator



def calculate_group_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """
    按实验组计算支付 A/B 实验的核心指标。

    参数
    ----
    data:
        已通过数据校验的用户级实验宽表。

    返回
    ----
    pd.DataFrame
        每一行代表一个实验组，每一列代表一个原子指标或派生指标。
    """
    metrics = (
        data.groupby("group", observed=True)
        .agg(
            assigned_users=("user_id", "size"),
            exposed_users=("exposed", "sum"),
            total_exposure_count=("exposure_count", "sum"),
            attempted_users=("attempted", "sum"),
            total_attempt_count=("attempt_count", "sum"),
            paid_users=("paid", "sum"),
            total_payment_amount=("payment_amount", "sum"),
            refunded_users=("refunded", "sum"),
            total_refund_amount=("refund_amount", "sum"),
            avg_payment_latency_ms=("payment_latency_ms", "mean"),
            new_users=("new_user", "sum"),
        )
        .sort_index()
    )

    # 漏斗转化指标
    metrics["exposure_rate"] = _safe_divide(
        metrics["exposed_users"],
        metrics["assigned_users"],
    )
    metrics["attempt_rate_given_exposed"] = _safe_divide(
        metrics["attempted_users"],
        metrics["exposed_users"],
    )
    metrics["payment_rate_given_attempt"] = _safe_divide(
        metrics["paid_users"],
        metrics["attempted_users"],
    )
    metrics["overall_payment_rate"] = _safe_divide(
        metrics["paid_users"],
        metrics["assigned_users"],
    )
    metrics["refund_rate_given_paid"] = _safe_divide(
        metrics["refunded_users"],
        metrics["paid_users"],
    )

    # 金额指标
    metrics["arpu"] = _safe_divide(
        metrics["total_payment_amount"],
        metrics["assigned_users"],
    )
    metrics["arppu"] = _safe_divide(
        metrics["total_payment_amount"],
        metrics["paid_users"],
    )
    metrics["net_payment_amount"] = (
        metrics["total_payment_amount"] - metrics["total_refund_amount"]
    )
    metrics["net_arpu"] = _safe_divide(
        metrics["net_payment_amount"],
        metrics["assigned_users"],
    )

    # 行为强度指标
    metrics["avg_exposures_per_exposed_user"] = _safe_divide(
        metrics["total_exposure_count"],
        metrics["exposed_users"],
    )
    metrics["avg_attempts_per_attempted_user"] = _safe_divide(
        metrics["total_attempt_count"],
        metrics["attempted_users"],
    )
    metrics["new_user_rate"] = _safe_divide(
        metrics["new_users"],
        metrics["assigned_users"],
    )

    return metrics


def format_metrics_for_display(metrics: pd.DataFrame) -> pd.DataFrame:
    """
    返回适合在控制台查看的指标表。

    比率转为百分比字符串，金额和时延保留两位小数。
    原始指标表不会被修改。
    """
    display = metrics.copy()

    rate_columns = [
        "exposure_rate",
        "attempt_rate_given_exposed",
        "payment_rate_given_attempt",
        "overall_payment_rate",
        "refund_rate_given_paid",
        "new_user_rate",
    ]

    for column in rate_columns:
        display[column] = display[column].map(
            lambda value: f"{value:.2%}" if pd.notna(value) else "N/A"
        )

    decimal_columns = [
        "total_payment_amount",
        "total_refund_amount",
        "avg_payment_latency_ms",
        "arpu",
        "arppu",
        "net_payment_amount",
        "net_arpu",
        "avg_exposures_per_exposed_user",
        "avg_attempts_per_attempted_user",
    ]
    
    for column in decimal_columns:
        display[column] = display[column].round(2)

    return display
