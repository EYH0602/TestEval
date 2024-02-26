import requests
import time
import os
import sys
from typing import Optional
import fire  

# Constants

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'}
MAX_RETRIES = 3
RETRY_BACKOFF = 2

def safe_request(url, headers, max_retries=MAX_RETRIES, timeout=10):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            elif response.status_code == 403 and "X-RateLimit-Reset" in response.headers:
                reset_time = int(response.headers["X-RateLimit-Reset"])
                sleep_time = max(reset_time - int(time.time()), 1)
                print(f"Rate limit exceeded. Waiting for {sleep_time} seconds.")
                time.sleep(sleep_time)
                 # Failed to fetch data after retries
            else:
                print(f"Request failed with status code {response.status_code}. Attempt {attempt + 1} of {max_retries}.")
                time.sleep(2 ** attempt)  
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}. Attempt {attempt + 1} of {max_retries}.")
             # Exponential backoff
            time.sleep(2 ** attempt) 
    return None 

def read_repos(file_path):
    with open(file_path, 'r') as file:
        repos = [line.strip() for line in file.readlines()]
    return repos

def get_commits_count(repo) -> Optional[int]:
    start_date = "2023-01-01T00:00:00Z"
    end_date = "2024-12-31T23:59:59Z"
    commits_url = f"{GITHUB_API}/repos/{repo}/commits?since={start_date}&until={end_date}&per_page=1"
    response = safe_request(commits_url, HEADERS)
    if response:
        if 'last' in response.links:
            last_page_url = response.links['last']['url']
            last_page_number = int(last_page_url.split('=')[-1])
            return last_page_number
        elif response.json():
            # Check if there's at least one commit in the specified range
            return 1
            # No commits in the specified date range
        return 0  
    return None

def get_bugs_count(repo) -> Optional[int]:
    bug_count = 0
    page = 1
    while True:
        issues_url = f"{GITHUB_API}/repos/{repo}/issues?labels=bug&state=all&page={page}&per_page=100"
        response = safe_request(issues_url, HEADERS)
        if response and response.status_code == 200:
            issues = response.json()
            if not issues:
                break
            for issue in issues:
                created_at = issue['created_at'][:10]  
                if "2023-01-01" <= created_at <= "2024-12-31":
                    bug_count += 1
            page += 1
        else:
            return None
    return bug_count

def write_output(repos_info, output_file):
    with open(output_file, 'w') as file:
        for repo, commits_count, bugs_count in repos_info:
            file.write(f"{repo.replace('/', ',')} , {commits_count} , {bugs_count}\n")

def main(input_file_path, output_file_path):
    repos = read_repos(input_file_path)
    repos_info = []

    for repo in repos:
        print(f"Processing {repo}...")
        commits_count = get_commits_count(repo)
        bugs_count = get_bugs_count(repo)
        repos_info.append((repo, commits_count, bugs_count))
    
    write_output(repos_info, output_file_path)
    print("Finished. Output written to", output_file_path)

if __name__ == "__main__":
    fire.Fire(main)
