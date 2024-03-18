"""
This script make collinearity analysiss between certain testing framework and the number of bug-related issues
"""

import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import fire
import os
import pandas as pd
import statsmodels.api as sm


def build_multilinear_regression_model(
    dataset_path: str = "./data/static_analysis_data/dataset.csv",
    output_dir: str = "images",
    choice: int = 7
):
    name = ""
    dataset = pd.read_csv(dataset_path)

    files_number = dataset["#files"]
    lines_number = dataset["#lines"]
    funcs_number = dataset["#funcs"]
    unit_test_funcs_number = dataset["#unit"]
    proptery_based_test_funcs_number = dataset["#proptery_based"]
    fuzz_target_number = dataset["#fuzz_target"]
    commits_number = dataset["#commits"]
    bug_related_issues_number = dataset["#bugs"]
    if choice == 1:
        X = pd.concat(
            [files_number, lines_number, funcs_number,commits_number, unit_test_funcs_number], axis=1
        )
        name = "unit_testing"
    elif choice == 2:
        X = pd.concat(
            [
                files_number,
                lines_number,
                funcs_number,
                commits_number,
                proptery_based_test_funcs_number,
            ],
            axis=1,
        )
        name = "property_based_testing"
    elif choice == 3:
        X = pd.concat(
            [files_number, lines_number, funcs_number,commits_number, fuzz_target_number], axis=1
        )
        name = "fuzz_testing"    
    elif choice == 4:
        X = pd.concat(
            [files_number, lines_number, funcs_number,commits_number, unit_test_funcs_number, proptery_based_test_funcs_number], axis=1
        )
        name = "unit_property_testing"  
    elif choice == 5:
        X = pd.concat(
            [files_number, lines_number, funcs_number,commits_number, unit_test_funcs_number, fuzz_target_number], axis=1
        )
        name = "unit_fuzz_testing"  
    elif choice == 6:
        X = pd.concat(
            [files_number, lines_number, funcs_number,commits_number, proptery_based_test_funcs_number, fuzz_target_number], axis=1
        )
        name = "property_fuzz_testing"       
    elif choice == 7:
        X = pd.concat(
            [
                files_number,
                lines_number,
                funcs_number,
                commits_number,
                unit_test_funcs_number,
                proptery_based_test_funcs_number,
                fuzz_target_number,
            ],
            axis=1,
        )
        name = "all_testing_fram"
    y = bug_related_issues_number

    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()

    print(model.summary())

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # residual analysis
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.scatter(model.fittedvalues, model.resid)
    plt.xlabel("Fitted values")
    plt.ylabel("Residuals")
    plt.title("Residuals & Fitted Value")

    plt.subplot(1, 2, 2)
    sm.qqplot(model.resid, line="s", ax=plt.gca())
    plt.title("Normal Q-Q")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/{name}_residual_analysis.png",dpi=500)
    plt.show()


# unit testing 1, property testing 2, fuzz testing 3, all testing 4
if __name__ == "__main__":
    fire.Fire(build_multilinear_regression_model)
