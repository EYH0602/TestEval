"""
This script checks if a repo fulfills certain requirements
Can customize what requirements to check and values to check against


References

Parts 1 and 2 of a medium blog explaining the query:
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ccbbb4e96d78
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ce2f73432f7

Repository Object:
https://docs.github.com/en/graphql/reference/objects#repository

"""

from datetime import datetime
import os
from typing import Callable, Optional
import fire
import json
import logging
from funcy_chain import Chain
from src.common import get_graphql_data, RepoMetadata, get_access_token


#### Requirement Callables ####
def req_enough_stars(metadata: RepoMetadata, req_stars: str = "10") -> bool:
    """Checks if Github repository has enough stars"""
    return metadata.stargazerCount >= int(req_stars)


def req_latest_commit(metadata: RepoMetadata, date_str: str = "2020-1-1") -> bool:
    """Checks if Github repository has a valid latest commit"""
    # latest_commit_date = datetime.fromisoformat(metadata["pushedAt"])
    date_values = metadata.pushedAt.split("T")[0].split("-")
    latest_commit_date = datetime(
        int(date_values[0]), int(date_values[1]), int(date_values[2])
    )
    date = date_str.split("-")
    req_date = datetime(int(date[0]), int(date[1]), int(date[2]))
    return latest_commit_date.date() > req_date.date()


def req_language(metadata: RepoMetadata, language: str = "python") -> bool:
    """Checks if Github repository has correct language"""
    if metadata.primaryLanguage is None:
        return False

    primary_lang: str = metadata.primaryLanguage["name"]
    return primary_lang.lower() == language.lower()


#### End Requirement Callables ####


def check_requirements(
    repo: str,
    requirements: list[Callable[[RepoMetadata, str], bool]],
    reqs: list[str],
    access_token: str,
    repo_data: Optional[RepoMetadata] = None,
) -> bool:
    """Checks if Github repository meets requirements

    Args:
        repo (str): Github repository in repo_owner/repo_name format
        requirements (list[callable]): List of requirement callables to check
            if repo meets requirement
        reqs (list[str]): List of values to check against for each callable
            - each req will be called with the callable of the same index in requirements

    Returns:
        bool: True if repo meets requirements, False otherwise
    """

    repo_query = repo.split("/")

    # Get repo data
    gql_format = """
    query {
        rateLimit {
            cost
            remaining
            resetAt
        }
        repository(name:"%s", owner:"%s"){
            id
            owner {
                login
            }
            name
            url
            isArchived
            isFork
            isMirror
            primaryLanguage {
                name
            }
            pushedAt
            stargazerCount
            object(expression: "HEAD:") {
                ... on Tree {
                    entries {
                        name
                        type
                    }
                }
            }
        }
    }
    """
    # Example of format of metadata:
    # {
    #   'data': {
    #       'rateLimit': {'cost': <cost>, 'remaining': <remaining>, 'resetAt': <ISO-8601 datetime>},
    #       'repository': {
    #           'primaryLanguage': <language>,
    #           'pushedAt': <ISO-8601 datetime>,
    #           'stargazerCount': <num_stars>
    #       }
    #   }
    # }
    if repo_data is None:  # Query if metadata is not provided
        metadata = get_graphql_data(
            gql_format % (repo_query[1], repo_query[0]), access_token
        )
        if metadata is None:
            logging.error("Fetching repo metadata error: None response")
            return False
        if "errors" in metadata:
            logging.error(f"Fetching repo metadata error: {metadata['errors']}")
            return False
        data: dict = metadata["data"]["repository"]
        if data is None:
            logging.warning(f"Response for repo {repo} is None")
            return False
        repo_data = RepoMetadata.from_dict(data)

    # If repo is archived, mirror, or fork, automatic fail
    if repo_data.isArchived:
        logging.warning(f"Repo {repo} is archived")
        return False
    if repo_data.isFork:
        logging.warning(f"Repo {repo} is fork")
        return False
    if repo_data.isMirror:
        logging.warning(f"Repo {repo} is mirror")
        return False

    # Check requirements
    for i, requirement in enumerate(requirements):
        if not requirement(repo_data, reqs[i]):
            logging.warning(
                f"{repo}: Error with req {requirement.__name__}"
                + f"with requirement {reqs[i]}",
            )
            return False

    # Save metadata to file to avoid repeat queries for repos that pass checks
    # print("Saving metadata")
    for key, value in repo_data.__dict__.items():
        meta_key_path = f"data/meta/{key}.json"
        if not os.path.exists(meta_key_path):
            os.system(f"touch {meta_key_path}")

        with open(f"data/meta/{key}.json", "r") as fp:
            try:
                dic = json.load(fp)
            except ValueError:
                dic = {}
        dic[repo] = value
        with open(meta_key_path, "w") as fp:
            json.dump(dic, fp)

    return True


# Map elements of checks_list to callables
CHECK_MAP: dict[str, Callable[[RepoMetadata, str], bool]] = {
    "stars": req_enough_stars,
    "latest commit": req_latest_commit,
    "language": req_language,
}


def main(
    reqs: list[str] | None = None,
    checks_list: list[str] | None = None,
    input_repo_list_path: str = "data/meta/oss_fuzz_python.jsonl",
    output_filter_result: str = "data/meta/oss_fuzz_python_filtered.jsonl",
    token: str = "oauth",
):
    """Pass checks_list and reqs with this : --checks_list='<list>' --reqs='<list>'
        Ex. --reqs='["0", "2020-1-1"]'template
        If checking Rust fuzz path, put null in place of where the req should be in the reqs list

    Args:
        repo_list_path (str, optional): path to list of repos metadata.
            Defaults to "data/meta/python.txt".
        checks_list (list[str], optional): _description_. Defaults to ["stars", "latest commit"].
        reqs (list[str], optional): _description_.
            Defaults to ["10", "2020-1-1"]. Year format should be <year>-<month>-<day>
    """

    # explicit None check to avoid dangerous-default-value caused by lists
    # see https://pylint.readthedocs.io/en/latest/user_guide/messages/warning/dangerous-default-value.html
    if checks_list is None:
        checks_list = ["stars", "latest commit"]
    if reqs is None:
        reqs = ["1000", "2020-1-1"]

    # if repo_id_list is a file then load lines
    # otherwise it is the id of a specific repo
    with open(input_repo_list_path, "r") as fp:
        repo_id_list: list[str] = [line.strip() for line in fp.readlines()]

    access_token = get_access_token(token)

    checks = [CHECK_MAP[check] for check in checks_list]
    test_eval_repos = (
        Chain(repo_id_list)
        .map(json.loads)
        .filter(lambda r: check_requirements(r["repo_id"], checks, reqs, access_token))
        .map(json.dumps)
        .value
    )
    with open(output_filter_result, "w") as fp:
        fp.write("\n".join(test_eval_repos))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
