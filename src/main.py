from pathlib import Path
from data_loader import load_payment_experiment_data
from metrics_calculator import calculate_group_metrics, format_metrics_for_display
from experiment_analyzer import compare_group_metrics

# 定义好要比较的指标

def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "payment_ab_experiment_100k.csv"

    data = load_payment_experiment_data(data_path)
    # 这个是检查，包括了数字和日期字段的类型转换和校验，以及基础校验和业务规则检查

    metrics = calculate_group_metrics(data)  #调用calculate_group_metrics计算各组指标
    display_metrics = format_metrics_for_display(metrics)  #调用format_metrics_for_display格式化指标以便在控制台显示
    print("支付实验各组核心指标：")
    print(display_metrics)
    print("下面计算差异")
    comparison = compare_group_metrics(metrics)  #调用compare_group_metrics计算组间差异
    print("组间差异比较：")
    print(comparison)

if __name__ == "__main__":
    main()