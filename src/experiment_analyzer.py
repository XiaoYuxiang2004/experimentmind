import pandas as pd


def compare_group_metrics(metrics):
    """
    比较实验组指标，返回一个包含比较结果的 DataFrame。
    """
    if "A" not in metrics.index or "B" not in metrics.index:
        raise ValueError("实验组 A 或 B 的指标缺失，无法进行比较。")

    comparison = pd.DataFrame(index=metrics.columns)   #创建一个空的 DataFrame，索引为指标名称
    comparison["A"] = metrics.loc["A"]
    comparison["B"] = metrics.loc["B"]
    comparison["Difference (B - A)"] = comparison["B"] - comparison["A"]
    comparison["Relative Difference (%)"] = (
        comparison["Difference (B - A)"] / comparison["A"].replace(0, pd.NA) * 100
    )

    return comparison