from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from openai import OpenAI


def _build_payment_analysis_payload(
    results: pd.DataFrame,
) -> dict:
    """
    将总体支付率检验结果转换成适合传给大模型的结构化字典。

    注意：
    这里传递的是未经字符串格式化的原始统计结果，
    避免模型混淆百分比、百分点和字符串。
    """
    metric_name = "overall_payment_rate"

    if metric_name not in results.index:
        raise ValueError(
            f"统计结果中缺少指标：{metric_name}"
        )

    row = results.loc[metric_name]

    return {
        "metric": metric_name,
        "metric_description": "总体支付率",
        "group_a": {
            "paid_users": int(row["a_paid_users"]),
            "total_users": int(row["a_total_users"]),
            "payment_rate": float(row["a_rate"]),
        },
        "group_b": {
            "paid_users": int(row["b_paid_users"]),
            "total_users": int(row["b_total_users"]),
            "payment_rate": float(row["b_rate"]),
        },
        "effect": {
            "absolute_change": float(
                row["absolute_change"]
            ),
            "relative_uplift": (
                None
                if pd.isna(row["relative_uplift"])
                else float(row["relative_uplift"])
            ),
        },
        "statistical_test": {
            "test_name": (
                "two_sample_proportion_z_test"
            ),
            "alternative": "two-sided",
            "z_statistic": float(
                row["z_statistic"]
            ),
            "p_value": float(row["p_value"]),
            "alpha": float(row["alpha"]),
            "significant": bool(
                row["significant"]
            ),
            "confidence_level": (
                1 - float(row["alpha"])
            ),
            "confidence_interval": {
                "lower": float(row["ci_lower"]),
                "upper": float(row["ci_upper"]),
            },
        },
    }


def generate_payment_experiment_report(
    results: pd.DataFrame,
) -> str:
    """
    调用大模型，根据 Python 已经计算好的统计结果，
    生成支付 A/B 实验解读。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = "https://ws-1p313dodlakx5z4u.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    model = "qwen-plus"

    if not api_key:
        raise ValueError(
            "未找到环境变量 DASHSCOPE_API_KEY。"
        )

    if not base_url:
        raise ValueError(
            "未找到环境变量 DASHSCOPE_BASE_URL。"
        )

    analysis_payload = (
        _build_payment_analysis_payload(results)
    )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    system_prompt = """
你是一名严谨的 A/B 实验分析师。

你的任务是解释由 Python 统计程序计算出的实验结果，
而不是重新计算统计指标。

必须遵守以下规则：

1. 只能使用用户提供的统计结果，不得编造数据。
2. 不得修改支付率、差异、p 值和置信区间。
3. absolute_change 表示 B 组减 A 组的绝对变化，
   输出时必须使用“百分点”。
4. relative_uplift 表示相对提升，输出时使用百分比。
5. p_value < alpha 时，才可以说结果具有统计显著性。
6. 不得把 p 值解释成“原假设为真的概率”。
7. 必须区分统计显著性和业务显著性。
8. 如果没有提供业务收益、实施成本和上线阈值，
   不得直接断言“应该全面上线”。
9. 置信区间跨过 0 时，必须指出效果方向尚不确定。
10. 使用简洁、专业、容易理解的中文。

请按照以下结构输出：

一、核心结论
二、关键数据
三、统计解释
四、业务意义
五、风险与下一步建议
""".strip()

    user_prompt = (
        "下面是 Python 程序已经计算好的实验结果：\n\n"
        + json.dumps(
            analysis_payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    report = response.choices[0].message.content

    if not report:
        raise RuntimeError(
            "大模型没有返回有效的实验报告。"
        )

    return report