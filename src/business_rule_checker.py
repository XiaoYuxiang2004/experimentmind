from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_loader import load_payment_experiment_data
from business_rules import validate_payment_business_rules


def check_payment_experiment_business_rules(file_path: str | Path) -> pd.DataFrame:
    """读取数据并执行业务规则检查。"""
    data = load_payment_experiment_data(file_path)
    validate_payment_business_rules(data)
    return data


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "sample_payment_experiment.csv"

    data = check_payment_experiment_business_rules(data_path)
    print("支付实验数据通过业务规则检查。")
    print(f"总用户数：{len(data)}")


if __name__ == "__main__":
    main()