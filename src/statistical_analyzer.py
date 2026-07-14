import pandas as pd
import numpy as np
from scipy.stats import norm

# 下面实现总体转化率overall_payment_rate的显著性检验

def analyze_overall_payment_rate(
    data: pd.DataFrame,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    对 A、B 两组的总体支付率进行两独立样本比例 Z 检验。

    原假设：
        H0: p_A = p_B

    备择假设：
        H1: p_A != p_B

    参数
    ----
    data:
        用户级实验宽表，必须包含 group、user_id、paid 字段。
    alpha:
        显著性水平，默认 0.05。

    返回
    ----
    pd.DataFrame
        包含两组比例、差异、相对提升、Z 值、p 值和置信区间。
    """

    # 1. 统计每个组的支付用户数和总用户数
    group_stats = (
        data.groupby("group", observed=True)
        .agg(
            paid_users=("paid", "sum"),
            total_users=("user_id", "size"),
        )
    )

    # 2. 确认AB组都存在
    required_groups = {"A", "B"}
    missing_groups = required_groups - set(group_stats.index)
    if missing_groups:
        raise ValueError(f"实验数据缺少必要的实验组：{missing_groups}")
    
    # 3. 计算支付率
    a_paid = int(group_stats.loc["A", "paid_users"])
    a_total = int(group_stats.loc["A", "total_users"])
    b_paid = int(group_stats.loc["B", "paid_users"])
    b_total = int(group_stats.loc["B", "total_users"])

    if a_total == 0 or b_total == 0:
        raise ValueError("A组或B组的总用户数为零，无法进行比例检验。")
    
    a_rate = a_paid / a_total
    b_rate = b_paid / b_total

    absolute_change = b_rate - a_rate

    relative_uplift = absolute_change / a_rate if a_rate != 0 else np.nan  # 避免除以零

    # 4. 计算合并比例和标准误差
    pooled_rate = (a_paid + b_paid) / (a_total + b_total)
    se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1 / a_total + 1 / b_total))

    if se == 0:
        raise ValueError("标准误差为零，无法进行 Z 检验。")
    
    # 5. 计算 Z 值和 p 值
    z_score = absolute_change / se

    p_value = 2 * norm.sf(abs(z_score))

    # 6. 计算置信区间
    se_ci = np.sqrt(a_rate * (1 - a_rate) / a_total + b_rate * (1 - b_rate) / b_total)  # 标准误差用于置信区间计算

    z_critical = norm.ppf(1 - alpha / 2)
    ci_lower = absolute_change - z_critical * se_ci
    ci_upper = absolute_change + z_critical * se_ci
    
    return pd.DataFrame(
        [
            {
                "metric": "overall_payment_rate",
                "a_paid_users": a_paid,
                "a_total_users": a_total,
                "a_rate": a_rate,
                "b_paid_users": b_paid,
                "b_total_users": b_total,
                "b_rate": b_rate,
                "absolute_change": absolute_change,
                "relative_uplift": relative_uplift,
                "z_statistic": z_score,
                "p_value": p_value,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "alpha": alpha,
                "significant": p_value < alpha,
            }
        ]
    ).set_index("metric")


def format_statistical_results_for_display(results: pd.DataFrame) -> pd.DataFrame:
    """
    格式化假设检验结果以便在控制台显示。

    参数
    ----
    results:
        假设检验结果 DataFrame。
    返回
    ----
    pd.DataFrame
        格式化后的结果。
    """
    formatted_results = results.copy()
    formatted_results["a_rate"] = (formatted_results["a_rate"] * 100).round(2).astype(str) + "%"
    formatted_results["b_rate"] = (formatted_results["b_rate"] * 100).round(2).astype(str) + "%"
    formatted_results["absolute_change"] = (formatted_results["absolute_change"] * 100).round(2).astype(str) + "百分点"
    formatted_results["relative_uplift"] = (formatted_results["relative_uplift"] * 100).round(2).astype(str) + "%"
    formatted_results["p_value"] = formatted_results["p_value"].apply(lambda x: f"{x:.4f}")
    formatted_results["ci_lower"] = (formatted_results["ci_lower"] * 100).round(2).astype(str) + "百分点"
    formatted_results["ci_upper"] = (formatted_results["ci_upper"] * 100).round(2).astype(str) + "百分点"
    formatted_results["interval"] = formatted_results.apply(
        lambda row: f"[{row['ci_lower']}, {row['ci_upper']}]", axis=1
    )

    return formatted_results[
        [
            "a_paid_users",
            "a_total_users",
            "a_rate",
            "b_paid_users",
            "b_total_users",
            "b_rate",
            "absolute_change",
            "relative_uplift",
            "z_statistic",
            "p_value",
            "interval",
            "alpha",
            "significant",
        ]
    ]