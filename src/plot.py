import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import fire

def generate_charts(df_path, bug_chart_path, commit_chart_path):
    """Generates and saves histograms for bug counts and commit counts.

    Args:
        df_path (str): Path to the CSV file containing the dataset.
        bug_chart_path (str): Path where the bug count histogram will be saved.
        commit_chart_path (str): Path where the commit count histogram will be saved.
    """
    try:
        df = pd.read_csv(df_path)
    except Exception as e:
        print(f"Failed to read {df_path}: {e}")
        return

    for column, chart_path in [('BugCount', bug_chart_path), ('CommitCount', commit_chart_path)]:
        plt.figure(figsize=(12, 8))
        sns.histplot(data=df, x=column, bins=20, kde=True, color='black')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig(chart_path, format='pdf')
        plt.close()

if __name__ == '__main__':
    fire.Fire(generate_charts)
