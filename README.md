# TestEval

Evaluating Python Testing Frameworks on Open-Source Software


## Usage

### Setup

```sh
source ./scripts/env.sh
pip3 install -r requirements.txt
```

And put your GitHub Personal access tokens in `./oauth`.

### Download Repos

### Get Usable Subset of CodeSearchNet

```sh
python3 scripts/check_repo_stats.py -i data/meta/codesearchnet.txt -o test_eval.txt
```

### Download

```sh
python3 scripts/download_repos.py -r data/meta/test_eval.txt --oroot data/repos
```