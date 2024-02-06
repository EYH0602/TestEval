"""common functions for scripts"""

import requests
import time
import logging
import os
import sys
import ast
import json
import signal
import datetime
import functools
import contextlib
from tqdm import tqdm
from typing import (
    Optional,
    Callable,
    List,
    Any,
    Dict,
    Iterable,
    Set,
    Tuple,
    TypeVar,
)
from pathos.multiprocessing import ProcessPool
import subprocess
from dataclasses import dataclass
from dacite import from_dict

# Functions from github ranking repo:
# https://github.com/EvanLi/Github-Ranking/blob/master/source/


@dataclass
class RepoMetadata:
    """Metadata Type returned by GitHub GraphQL API"""

    id: str
    owner: dict
    name: str
    url: str
    isArchived: bool  # pylint: disable=invalid-name
    isFork: bool  # pylint: disable=invalid-name
    isMirror: bool  # pylint: disable=invalid-name
    primaryLanguage: dict  # pylint: disable=invalid-name
    pushedAt: str  # pylint: disable=invalid-name
    stargazerCount: int  # pylint: disable=invalid-name
    object: dict

    @staticmethod
    def from_dict(metadata_dict: dict):
        return from_dict(data_class=RepoMetadata, data=metadata_dict)


def get_access_token(oauth_path: str):
    with open(oauth_path, "r") as f:
        access_token = f.read().strip()
    return access_token


def get_graphql_data(gql: str, access_token: str) -> dict:
    """use graphql to get data


    Args:
        gql (str): graph ql query
        access_token: access token to GitHub

    Returns:
        (dict): response from GitHub
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Authorization": f"bearer {access_token}",
    }
    s = requests.session()
    # s.keep_alive = False  # don't keep the session
    graphql_api = "https://api.github.com/graphql"
    r: requests.Response
    for _ in range(5):
        time.sleep(2)  # not get so fast
        try:
            # # disable InsecureRequestWarning of verify=False,
            # requests.packages.urllib3.disable_warnings()
            r = requests.post(
                url=graphql_api, json={"query": gql}, headers=headers, timeout=30
            )
            if r.status_code != 200:
                logging.warning(
                    f"Can not retrieve from {gql}."
                    + f"Response status is {r.status_code},"
                    + f"content is {r.content.decode('utf-8')}."
                )
            else:
                break
        except Exception as e:
            print(e)
            time.sleep(5)

    response: dict = r.json()
    return response
