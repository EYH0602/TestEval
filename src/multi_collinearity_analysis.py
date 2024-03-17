"""
This script make collinearity analysiss between certain testing framework and the number of bug-related issues
"""

import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns
import fire
import os
import pandas as pd
import statsmodels.api as sm

def build_multilinear_regression_model(
    dataset_path: str = "./data/static_analysis_data/dataset.csv",
    barchart_name: str = "correlation_coefficient",
    heatmap_name: str = "collinearity_heatmap",
    output_dir: str = "images",
    choice: int = 1
):

    dataset = pd.read_csv(dataset_path)

    files_number = dataset["#files"]
    lines_number = dataset["#lines"]
    funcs_number = dataset["#funcs"]
    unit_test_funcs_number = dataset["#unit"]
    proptery_based_test_funcs_number = dataset["#proptery_based"]
    fuzz_target_number = dataset["#fuzz_target"]
    if choice == 1:
        X = pd.concat([files_number,lines_number,funcs_number,unit_test_funcs_number],axis=1)
    elif choice == 2:
        X = pd.concat([files_number,lines_number,funcs_number,proptery_based_test_funcs_number],axis=1)
    elif choice == 3:
        X = pd.concat([files_number,lines_number,funcs_number,fuzz_target_number],axis=1)
    elif choice == 4:
        X = pd.concat([files_number,lines_number,funcs_number,unit_test_funcs_number,proptery_based_test_funcs_number,fuzz_target_number],axis=1)
    # X = dataset[["#files", "#lines", "#funcs", "#unit"]] 
    y = fuzz_target_number  

    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()

    print(model.summary())

    #residual analysis
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.scatter(model.fittedvalues, model.resid)
    plt.xlabel('Fitted values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')

    plt.subplot(1, 2, 2)
    sm.qqplot(model.resid, line='s', ax=plt.gca())
    plt.title('Normal Q-Q')

    plt.tight_layout()
    plt.savefig(f"{output_dir}/residual_analysis.png")
    plt.show()

#unit testing 1, property testing 2, fuzz testing 3, all testing 4
if __name__ == "__main__":
    fire.Fire(build_multilinear_regression_model)
