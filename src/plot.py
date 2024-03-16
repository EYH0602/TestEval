import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import fire

def generate_charts(df_path, bug_chart_path, commit_chart_path):
    df = pd.read_csv(df_path)
    top_20_by_bug_count = df.nlargest(20, 'BugCount')
    top_20_by_commit_count = df.nlargest(20, 'CommitCount')
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x='BugCount', y='RepoName', data=top_20_by_bug_count, palette='viridis')
    plt.title('Top 20 Repositories by Bug Count')
    plt.xlabel('Bug Count')
    plt.ylabel('Repository')
    plt.tight_layout()
    plt.savefig(bug_chart_path)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x='CommitCount', y='RepoName', data=top_20_by_commit_count, palette='viridis')
    plt.title('Top 20 Repositories by Commit Count')
    plt.xlabel('Commit Count')
    plt.ylabel('Repository')
    plt.tight_layout()
    plt.savefig(commit_chart_path)

if __name__ == '__main__':
    fire.Fire(generate_charts)
