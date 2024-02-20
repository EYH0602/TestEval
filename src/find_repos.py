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
from typing import Optional
import json
from funcy import lfilter


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


def load_proj_config(proj_path: str) -> Optional[dict]:
    """load a project's configuration to dict

    Args:
        proj_path (str): path to the oss-fuzz supported project

    Returns:
        Optional[dict]: configuration, None if key "language" not in it
    """
    config_path = os.path.join(proj_path, "project.yaml")
    with open(config_path, "r") as fp:
        config: dict[str, str | int] = yaml.safe_load(fp)

    config["#fuzz_target"] = len(
        [s for s in os.listdir(proj_path) if s.endswith(".py")]
    )

    return config if "language" in config else None


def to_repo_json(config: dict[str, str]):
    url = config["main_repo"].strip("/")
    j = config.copy()
    j["repo_id"] = "/".join(url.split("/")[-2:])
    return j


def get_oss_fuzz_projects(language: str = "python") -> list[str]:
    oss_fuzz_dir = os.path.join(os.environ["WORKDIR"], "oss-fuzz")
    projects_dir = os.path.join(oss_fuzz_dir, "projects")

    proj_list: list[str] = (
        Chain(os.listdir(projects_dir))
        .map(lambda p: os.path.join(projects_dir, p))
        .map(load_proj_config)
        .filter(None)
        .filter(lambda config: config["language"] == language)
        .map(to_repo_json)
        .map(json.dumps)
        .value
    )

    return proj_list


# Pass checks_list and reqs with this template: --checks_list='<list>' --reqs='<list>'
# Ex. --reqs='["0", "2020-1-1"]'
# If checking Rust fuzz path, put null in place of where the req should be in the reqs list
def main(language: str = "python", output_file: str = "output.jsonl"):
    oss_fuzz_projects = get_oss_fuzz_projects(language.lower())
    logging.info(f"Find {len(oss_fuzz_projects)} projects in OSS-Fuzz projects")
    with open(output_file, "w") as fp:
        fp.write("\n".join(oss_fuzz_projects))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
