"""
script to filter projects from OSS_Fuzz
"""

from collections import OrderedDict
import fire
import os
import logging
from funcy_chain import Chain
import yaml
from check_repo_stats import check_requirements, CHECK_MAP
from common import RepoMetadata, get_access_token, get_graphql_data


def save_repos_to_file(language: str, repos_list: list[str]) -> None:
    """
    Save the repository names to a file named new_<language>.txt in the data/repo_meta directory.
    """
    repo_list_path = f"data/meta/{language.lower()}.txt"

    # Using "a" to append to the file if it already exists
    with open(repo_list_path, "a") as file:
        for repo_name in repos_list:
            file.write(repo_name + "\n")

    # use OrderedDict to reduce repetition and keep the ordering
    with open(repo_list_path, "r") as file:
        unique_repos = OrderedDict.fromkeys(file.read().splitlines())

    # write back to original txt
    with open(repo_list_path, "w") as file:
        for repo in unique_repos:
            file.write(f"{repo}\n")


def load_proj_config(proj_path: str) -> dict:
    config_path = os.path.join(proj_path, "project.yaml")
    with open(config_path, "r") as fp:
        config: dict[str, str] = yaml.safe_load(fp)

    return config


def to_repo_id(config: dict[str, str]) -> str:
    url = config["main_repo"]
    return "/".join(url.split("/")[-2:])


def get_oss_fuzz_projects(language: str = "python") -> list[str]:
    oss_fuzz_dir = os.path.join(os.environ["WORKDIR"], "oss-fuzz")
    projects_dir = os.path.join(oss_fuzz_dir, "projects")

    proj_list: list[str] = (
        Chain(os.listdir(projects_dir))
        .map(lambda p: os.path.join(projects_dir, p))
        .map(load_proj_config)
        .filter(lambda config: config["language"] == language)
        .map(to_repo_id)
        .value
    )

    return proj_list


# Pass checks_list and reqs with this template: --checks_list='<list>' --reqs='<list>'
# Ex. --reqs='["0", "2020-1-1"]'
# If checking Rust fuzz path, put null in place of where the req should be in the reqs list
def main(
    language: str = "python",
    checks_list: list[str] | None = None,
    reqs: list[str] | None = None,  # Year format should be <year>-<month>-<day>
    oauth: str = "oauth",
):
    if checks_list is None:
        checks_list = ["stars", "latest commit"]
    if reqs is None:
        reqs = ["1000", "2020-1-1"]
    # Set up requirement callables and reqs
    checks = [CHECK_MAP[check] for check in checks_list]
    access_token = get_access_token(oauth)

    print(get_oss_fuzz_projects(language.lower()))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
