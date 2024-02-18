# TestEval

Evaluating Python Testing Frameworks on Open-Source Software


## Usage

### Setup

```sh
source ./src/env.sh
pip3 install -r requirements.txt
git submodule init
git submodule update
```

And put your GitHub Personal access tokens in `./oauth`.

### Download Repos

### Get Repo List

```sh
python3 src/find_repos.py -o data/meta/oss_fuzz_python.txt # find Python repos from OSS-Fuzz
python3 src/check_repo_stats.py -i data/meta/oss_fuzz_python.txt -o oss_fuzz_python_filtered.txt
```

### Download

```sh
cd data && mkdir repos && cd ..
python3 src/download_repos.py -i data/meta/oss_fuzz_python_filtered.txt --oroot data/repos
```
