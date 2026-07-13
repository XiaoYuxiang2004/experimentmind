from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from data_validator import validate_payment_experiment_data

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

    return data


# 再打印摘要
def print_basic_summary(data: pd.DataFrame) -> None:
    """打印支付实验数据的基础摘要。"""
    print("支付实验数据读取并验证成功！")  #因为 validate_payment_experiment_data 函数会抛出异常，所以如果执行到这里，说明数据是有效的。

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