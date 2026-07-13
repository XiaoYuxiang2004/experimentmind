from pathlib import Path

import pandas as pd


def load_payment_experiment_data(file_path: str | Path) -> pd.DataFrame:
    """读取支付 A/B 实验 CSV 数据。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到数据文件：{path}")

    data = pd.read_csv(path)

    if data.empty:
        raise ValueError("实验数据文件为空。")

    return data


def print_basic_summary(data: pd.DataFrame) -> None:
    """打印支付实验数据的基础摘要。"""
    print("支付实验数据读取成功！")
    print(f"总用户数：{len(data)}")
    print(f"字段数量：{data.shape[1]}")
    print(f"字段列表：{data.columns.tolist()}")

    print("\n各实验组用户数：")
    print(data.groupby("group").size())

    print("\n各实验组支付漏斗原子指标：")
    group_summary = data.groupby("group").agg(
        users=("user_id", "nunique"),
        exposed_users=("exposed", "sum"),
        attempted_users=("attempted", "sum"),
        paid_users=("paid", "sum"),
        total_payment_amount=("payment_amount", "sum"),
        refunded_users=("refunded", "sum"),
        total_refund_amount=("refund_amount", "sum"),
    )

    print(group_summary)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "sample_payment_experiment.csv"

    experiment_data = load_payment_experiment_data(data_path)
    print_basic_summary(experiment_data)