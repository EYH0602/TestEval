import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns
import fire
def main():
    dataset_path = './data/static_analysis_data/dataset.csv'
    dataset = pd.read_csv(dataset_path)

    funcs_number = dataset['#funcs']
    unit_test_funcs_number = dataset['#unit']
    proptery_based_test_funcs_number = dataset['#proptery_based']
    fuzz_target_number = dataset['#fuzz_target']


    correlation_unit_funcs = pearsonr(funcs_number, unit_test_funcs_number)[0]
    correlation_proptery_based_funcs = pearsonr(funcs_number, proptery_based_test_funcs_number)[0]
    correlation_fuzz_target_funcs = pearsonr(funcs_number, fuzz_target_number)[0]

    correlations = [correlation_unit_funcs,correlation_proptery_based_funcs,correlation_fuzz_target_funcs]
    predictors = ["unit test functions number","property-based test functions number","fuzz target number"]
    
    print(f"Correlation Coefficient of funcs number and unit test functions number : {correlation_unit_funcs:.4f}")
    print(f"Correlation Coefficient of funcs number and property-based test functions number : {correlation_proptery_based_funcs:.4f}")
    print(f"Correlation Coefficient of funcs number and fuzz target number : {correlation_fuzz_target_funcs:.4f}")

    plt.figure(figsize=(10, 6))
    plt.bar(predictors, correlations, color=['blue', 'green', 'red'])

    plt.title('Correlation with Funcs Number')
    plt.xlabel('Predictors')
    plt.ylabel('Pearson Correlation Coefficient')

    for i, corr in enumerate(correlations):
        plt.text(i, corr if corr > 0 else corr - 0.02, f'{corr:.4f}', ha = 'center', va = 'bottom' if corr > 0 else 'top')

    plt.savefig("./Analysis/correlation_coefficient.png",dpi=500)
    plt.show()
    
    columns_of_interest = ['#funcs', '#unit', '#proptery_based', '#fuzz_target']

    correlation_matrix = dataset[columns_of_interest].corr()

    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=.5)
    plt.title('Predictors Correlation Heatmap')

    plt.savefig("./Analysis/collinearity_heatmap.png",dpi=500)
    plt.show()

if __name__ == "__main__":
    fire.Fire(main)