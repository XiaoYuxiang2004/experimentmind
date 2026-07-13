from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from business_rules import validate_payment_business_rules
from data_validator import validate_payment_experiment_data
from data_validator import validate_payment_experiment_columns

from metrics_calculator import (calculate_group_metrics, format_metrics_for_display)

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

# 这个函数将被用在 load_payment_experiment_data 中，确保日期字段被正确解析为 datetime 类型，并在发现无法解析的值时抛出异常。
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

# 这个函数将被用在 load_payment_experiment_data 中，确保数值字段被正确解析为数值类型，并在发现无法解析的值时抛出异常。
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

# 先做基础校验，再做业务规则检查，这个是data_loader.py的主要功能
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

    validate_payment_experiment_columns(data)


    data = _coerce_datetime_columns(data)
    data = _coerce_numeric_columns(data)

    # 上面两步是做了日期和数值字段的类型转换和校验，下面做基础校验和业务规则检查

    validate_payment_experiment_data(data)
    # 做了基础校验
    validate_payment_business_rules(data)
    # 做了业务规则检查

    print("支付实验数据基础校验和业务规则检查均已通过。")

    return data


# # 再打印摘要
# def print_basic_summary(data: pd.DataFrame) -> None:
#     """打印支付实验数据的基础摘要。"""
#     metrics = calculate_group_metrics(data)  # 计算各组指标
#     display_metrics = format_metrics_for_display(metrics) # 格式化指标以便在控制台显示
#     print("\n支付实验各组核心指标：")
#     print(display_metrics)



# if __name__ == "__main__":
#     project_root = Path(__file__).resolve().parents[1]   # 获取项目根目录
#     data_path = project_root / "data" / "payment_ab_experiment_100k.csv"  # 数据文件路径

#     experiment_data = load_payment_experiment_data(data_path)  # 加载并验证数据
#     print_basic_summary(experiment_data)