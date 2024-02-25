"""
This script make collinearity analysis based on 4 predictors for our linear regression
"""

import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns
import fire
import os


def collinearity_analysis(
    dataset_path: str = "./data/static_analysis_data/dataset.csv",
    barchart_name: str = "correlation_coefficient",
    heatmap_name: str = "collinearity_heatmap",
    output_dir: str = "images",
):

    dataset = pd.read_csv(dataset_path)

    funcs_number = dataset["#funcs"]
    unit_test_funcs_number = dataset["#unit"]
    proptery_based_test_funcs_number = dataset["#property_based"]
    fuzz_target_number = dataset["#fuzz_target"]

    correlation_unit_funcs = pearsonr(funcs_number, unit_test_funcs_number)[0]
    correlation_proptery_based_funcs = pearsonr(
        funcs_number, proptery_based_test_funcs_number
    )[0]
    correlation_fuzz_target_funcs = pearsonr(funcs_number, fuzz_target_number)[0]

    correlations = [
        correlation_unit_funcs,
        correlation_proptery_based_funcs,
        correlation_fuzz_target_funcs,
    ]
    predictors = ["#unit", "#proptery_based", "#fuzz_target"]

    print(
        f"Correlation Coefficient of funcs number and unit test functions number : {correlation_unit_funcs:.4f}"
    )
    print(
        f"Correlation Coefficient of funcs number and property-based test functions number : {correlation_proptery_based_funcs:.4f}"
    )
    print(
        f"Correlation Coefficient of funcs number and fuzz target number : {correlation_fuzz_target_funcs:.4f}"
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.figure(figsize=(10, 6))
    plt.bar(predictors, correlations, color=["blue", "green", "red"])
    font = {
        "family": "serif",
        "color": "darkred",
        "weight": "normal",
        "size": 16,
    }
    plt.xlabel("Predictors", fontdict=font)
    plt.ylabel("Pearson Correlation Coefficient", fontdict=font)
    for i, corr in enumerate(correlations):
        plt.text(
            i,
            corr if corr > 0 else corr - 0.014,
            f"{corr:.4f}",
            ha="center",
            va="bottom",
        )
    plt.savefig(f"./{output_dir}/{barchart_name}.pdf", dpi=500, bbox_inches="tight")
    plt.show()

    columns_of_interest = ["#funcs", "#unit", "#proptery_based", "#fuzz_target"]
    correlation_matrix = dataset[columns_of_interest].corr()

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", linewidths=0.5)
    plt.savefig(f"./{output_dir}/{heatmap_name}.pdf", dpi=500, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    fire.Fire(collinearity_analysis)
