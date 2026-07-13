from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

# 支付实验数据的必要字段
REQUIRED_PAYMENT_EXPERIMENT_COLUMNS = (
    "user_id",
    "group",
    "assigned_at",
    "exposed",
    "exposure_count",
    "first_exposure_at",
    "attempted",
    "attempt_count",
    "paid",
    "payment_amount",
    "refunded",
    "refund_amount",
    "payment_latency_ms",
    "device",
    "new_user",
)

# 允许为空的字段：用户未曝光时没有首曝光时间
OPTIONAL_NULLABLE_COLUMNS = (
    "first_exposure_at",
    "payment_latency_ms" # 用户未支付时没有支付延迟
)

# 这些字段在当前数据口径下必须有值
REQUIRED_NON_NULL_COLUMNS = tuple(
    column
    for column in REQUIRED_PAYMENT_EXPERIMENT_COLUMNS
    if column not in OPTIONAL_NULLABLE_COLUMNS
)

# 支付实验数据的二元字段
BINARY_COLUMNS = (
    "exposed",
    "attempted",
    "paid",
    "refunded",
    "new_user",
)

EXPECTED_GROUPS = frozenset({"A", "B"})  # 实验分组的期望值


def validate_payment_experiment_columns(
    data: pd.DataFrame,
    required_columns: Iterable[str] = REQUIRED_PAYMENT_EXPERIMENT_COLUMNS,
) -> None:
    """确保支付实验数据包含全部必要字段。"""
    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(f"实验数据缺少必要字段：{missing_columns}")


def validate_required_values_not_missing(
    data: pd.DataFrame,
    required_columns: Iterable[str] = REQUIRED_NON_NULL_COLUMNS,  # 这里剔除了 first_exposure_at，因为它在用户未曝光时可以为空
) -> None:
    """确保必要字段中没有缺失值。"""
    columns = list(required_columns)
    missing_counts = data[columns].isna().sum()

    missing_summary = {
        column: int(count)
        for column, count in missing_counts.items()
        if count > 0
    }

    if missing_summary:
        raise ValueError(
            f"必要字段中存在缺失值：{missing_summary}"
        )


def validate_experiment_groups(
    data: pd.DataFrame,
    expected_groups: frozenset[str] = EXPECTED_GROUPS,
) -> None:
    """确保实验数据只包含 A、B 两组，并且两组均存在。"""
    actual_groups = set(data["group"].unique())

    invalid_groups = actual_groups - expected_groups
    missing_groups = expected_groups - actual_groups

    error_messages = []

    if invalid_groups:
        error_messages.append(
            f"发现非法实验分组：{sorted(invalid_groups)}"
        )

    if missing_groups:
        error_messages.append(
            f"实验数据缺少分组：{sorted(missing_groups)}"
        )

    if error_messages:
        raise ValueError("；".join(error_messages))


def validate_binary_columns(
    data: pd.DataFrame,
    binary_columns: Iterable[str] = BINARY_COLUMNS,
) -> None:
    """确保二元字段只包含 0 和 1。"""
    invalid_values_by_column = {}

    for column in binary_columns:
        invalid_values = [
            value
            for value in data[column].unique().tolist()
            if value not in (0, 1)
        ]

        if invalid_values:
            invalid_values_by_column[column] = invalid_values

    if invalid_values_by_column:
        raise ValueError(
            f"二元字段只能包含 0 和 1：{invalid_values_by_column}"
        )


def validate_unique_users(data: pd.DataFrame) -> None:
    """确保用户级实验表中每个用户只出现一次。"""
    duplicate_mask = data["user_id"].duplicated(keep=False)

    if duplicate_mask.any():
        duplicate_user_ids = (
            data.loc[duplicate_mask, "user_id"]
            .drop_duplicates()
            .tolist()
        )

        displayed_ids = duplicate_user_ids[:10]

        raise ValueError(
            "用户级实验数据中存在重复用户："
            f"{displayed_ids}，共 {len(duplicate_user_ids)} 个重复用户"
        )


def validate_payment_experiment_data(data: pd.DataFrame) -> None:
    """执行支付实验数据的基础质量检查。"""
    validate_payment_experiment_columns(data)
    validate_required_values_not_missing(data)
    validate_experiment_groups(data)
    validate_binary_columns(data)
    validate_unique_users(data)