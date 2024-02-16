"""common functions for scripts"""

import requests
import time
import logging
import json
import signal
import datetime
import contextlib
from typing import Optional, Callable
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
    primaryLanguage: dict | None  # pylint: disable=invalid-name
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


def get_graphql_data(gql: str, access_token: str) -> Optional[dict]:
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
    # s = requests.session()
    # s.keep_alive = False  # don't keep the session
    graphql_api = "https://api.github.com/graphql"
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
                    f"Can not retrieve from {gql}.\n"
                    + f"Response status is {r.status_code},\n"
                    + f"content is {r.content.decode('utf-8')}."
                )
            else:
                response: dict = r.json()
                return response

        except Exception as e:
            logging.warning(e)
            time.sleep(5)

    return None


class Timing:
    """providing timing as context or functions"""

    queue: list = []

    def __enter__(self):
        self.tic()
        return self

    def __exit__(self, *args):
        self.tac()

    @staticmethod
    def tic():
        Timing.queue.append(time.time())

    @staticmethod
    def tac():
        assert Timing.queue, "Call Timing.tic before"
        start_at = Timing.queue.pop()
        print(f"Elapsed {datetime.timedelta(seconds=time.time() - start_at)}")


def log_or_skip(path: Optional[str] = None, handler=json.dumps, **kwargs):
    """log kwargs if path is provided with handler for preprocessing"""
    if not path:
        return
    with open(path, "a") as outfile:
        to_log = kwargs
        if handler:
            to_log = handler(to_log)
        outfile.write(f"{to_log}\n")


def wrap_repo(name: str):
    """wrap repo name from username/repo into username+repo"""
    return "+".join(name.split("/"))


class TimeoutException(Exception):
    """Wrapper Exception for Frontend Timeout"""

    pass  # pylint: disable=unnecessary-pass


@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def timestamp(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(fmt)


def timeout_wrapper(handler: Callable, timeout: int = -1):
    """return None if timeout instead of raising error"""

    def inner(*args, **kwargs):
        if timeout <= 0:
            return handler(*args, **kwargs)
        try:
            with time_limit(timeout):
                return handler(*args, **kwargs)
        except TimeoutException:
            pass
        return None

    return inner


def run_with_timeout(func: Callable):
    """run a function with timeout"""

    def wrapper(*args, timeout=-1, **kwargs):
        if timeout <= 0:
            return func(*args, **kwargs)
        try:
            with time_limit(timeout):
                return func(*args, **kwargs)
        except TimeoutException:
            pass
        return None

    return wrapper
