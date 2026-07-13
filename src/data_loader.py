from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from business_rules import validate_payment_business_rules
from data_validator import validate_payment_experiment_data

DATE_COLUMNS = ("assigned_at", "first_exposure_at")
DATE_PARSE_FORMAT = "%Y-%m-%d %H:%M:%S"
NUMERIC_COLUMNS = (
    "exposed",
    "exposure_count",
    "attempted",
    "attempt_count",
    "paid",
    "payment_amount",
    "refunded",
    "refund_amount",
    "payment_latency_ms",
    "new_user",
)


def _coerce_datetime_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    将日期字段转换为 datetime 类型，并检查是否存在无法解析的值。
    """
    for column in DATE_COLUMNS:
        original_values = data[column]
        converted_values = pd.to_datetime(
            original_values,
            errors="coerce",
            format=DATE_PARSE_FORMAT,
        )

        invalid_mask = original_values.notna() & converted_values.isna()
        if invalid_mask.any():
            invalid_values = original_values.loc[invalid_mask].drop_duplicates().tolist()
            raise ValueError(f"日期字段 {column} 存在无法解析的值：{invalid_values}")

        data[column] = converted_values

    return data


def _coerce_numeric_columns(data: pd.DataFrame) -> pd.DataFrame:
    '''
    将数值字段转换为数值类型，并检查是否存在无法解析的值。
    '''
    for column in NUMERIC_COLUMNS:
        original_values = data[column]
        converted_values = pd.to_numeric(original_values, errors="coerce")

        invalid_mask = original_values.notna() & converted_values.isna()
        if invalid_mask.any():
            invalid_values = original_values.loc[invalid_mask].drop_duplicates().tolist()
            raise ValueError(f"数值字段 {column} 存在无法解析的值：{invalid_values}")

        data[column] = converted_values

    return data

# 先检查
def load_payment_experiment_data(
    file_path: str | Path,
) -> pd.DataFrame:
    """读取并验证支付 A/B 实验 CSV 数据。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到数据文件：{path}")

    if not path.is_file():
        raise ValueError(f"指定路径不是文件：{path}")

    try:
        data = pd.read_csv(path)
    except EmptyDataError as error:
        raise ValueError("实验数据文件完全为空。") from error

    if data.empty:
        raise ValueError("实验数据只有表头，没有用户记录。")

    validate_payment_experiment_data(data)

    data = _coerce_datetime_columns(data)
    data = _coerce_numeric_columns(data)

    validate_payment_business_rules(data)

    print("支付实验数据基础校验和业务规则检查均已通过。")

    return data


# 再打印摘要
def print_basic_summary(data: pd.DataFrame) -> None:
    """打印支付实验数据的基础摘要。"""
    print("支付实验数据读取、校验并分析成功。")

    print("\n各实验组用户数：")
    print(data.groupby("group").size())

    print("\n各实验组支付漏斗原子指标：")
    group_summary = data.groupby("group").agg(
        users=("user_id", "nunique"),  # 计算唯一用户数
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

    print(group_summary)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]   # 获取项目根目录
    data_path = project_root / "data" / "sample_payment_experiment.csv"

    experiment_data = load_payment_experiment_data(data_path)
    print_basic_summary(experiment_data)