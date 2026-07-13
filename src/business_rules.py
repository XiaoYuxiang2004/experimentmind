from __future__ import annotations

import pandas as pd


def _format_user_sample(user_ids: list[str], limit: int = 10) -> str:
    displayed = user_ids[:limit]
    suffix = "" if len(user_ids) <= limit else f"，共 {len(user_ids)} 个用户"
    return f"涉及 {len(user_ids)} 个用户：{displayed}{suffix}"


def _collect_violation_users(data: pd.DataFrame, mask: pd.Series) -> list[str]:
    return data.loc[mask, "user_id"].drop_duplicates().astype(str).tolist()


def validate_payment_business_rules(data: pd.DataFrame) -> None:
    """根据数据字典检查支付实验的跨字段业务规则。"""
    violation_messages: list[str] = []

    rules = [
        ("paid <= attempted <= exposed", data["paid"] <= data["attempted"]),
        ("attempted <= exposed", data["attempted"] <= data["exposed"]),
        ("refunded <= paid", data["refunded"] <= data["paid"]),
        (
            "exposed = 0 时 exposure_count = 0",
            ~((data["exposed"] == 0) & (data["exposure_count"] != 0)),
        ),
        (
            "exposed = 1 时 exposure_count >= 1",
            ~((data["exposed"] == 1) & (data["exposure_count"] < 1)),
        ),
        (
            "exposed = 0 时 first_exposure_at 为空",
            ~((data["exposed"] == 0) & (data["first_exposure_at"].notna())),
        ),
        (
            "exposed = 1 时 first_exposure_at 非空",
            ~((data["exposed"] == 1) & (data["first_exposure_at"].isna())),
        ),
        (
            "exposed = 1 时 assigned_at <= first_exposure_at",
            ~(
                (data["exposed"] == 1)
                & data["first_exposure_at"].notna()
                & (data["assigned_at"] > data["first_exposure_at"])
            ),
        ),
        (
            "attempted = 0 时 attempt_count = 0",
            ~((data["attempted"] == 0) & (data["attempt_count"] != 0)),
        ),
        (
            "attempted = 1 时 attempt_count >= 1",
            ~((data["attempted"] == 1) & (data["attempt_count"] < 1)),
        ),
        (
            "paid = 0 时 payment_amount = 0",
            ~((data["paid"] == 0) & (data["payment_amount"] != 0)),
        ),
        (
            "paid = 1 时 payment_amount > 0",
            ~((data["paid"] == 1) & (data["payment_amount"] <= 0)),
        ),
        (
            "paid = 0 时 payment_latency_ms 为空",
            ~((data["paid"] == 0) & (data["payment_latency_ms"].notna())),
        ),
        (
            "paid = 1 时 payment_latency_ms > 0",
            ~(
                (data["paid"] == 1)
                & (data["payment_latency_ms"].isna() | (data["payment_latency_ms"] <= 0))
            ),
        ),
        (
            "refunded = 0 时 refund_amount = 0",
            ~((data["refunded"] == 0) & (data["refund_amount"] != 0)),
        ),
        (
            "refunded = 1 时 refund_amount > 0",
            ~((data["refunded"] == 1) & (data["refund_amount"] <= 0)),
        ),
        (
            "refund_amount <= payment_amount",
            data["refund_amount"] <= data["payment_amount"],
        ),
    ]

    for message, passed_mask in rules:
        if passed_mask.all():
            continue

        failed_user_ids = _collect_violation_users(data, ~passed_mask)
        violation_messages.append(
            f"规则不通过 - {message}；{_format_user_sample(failed_user_ids)}"
        )

    if violation_messages:
        raise ValueError("；".join(violation_messages))