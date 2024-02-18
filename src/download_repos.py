"""Script to download repos from GitHub"""

import os
import fire
import time
import random
import tarfile
import requests
from tqdm import tqdm
from github import Github, Auth
from github.Repository import Repository
from github.Commit import Commit
from github.GitRelease import GitRelease
from github.Tag import Tag
from github.GithubException import GithubException
from typing import Tuple, Optional
from returns.result import Result, Success, Failure
from enum import IntEnum
import logging

from common import (
    log_or_skip,
    wrap_repo,
    time_limit,
    TimeoutException,
    get_access_token,
)


class DownloadErrorCode(IntEnum):
    """Status Code for download repo"""

    FETCH_REPO_FAILED = 0
    FETCH_ARCHIVE_FAILED = 1
    DOWNLOAD_ARCHIVE_FAILED = 2
    TARFILE_EXTRACT_FAILED = 3


def fetch_repo(
    repo_id: str, timeout: int, hub: Optional[Github]
) -> Result[Repository, DownloadErrorCode]:
    """fetch a repo"""
    hub = hub if hub is not None else Github()
    try:
        with time_limit(timeout):
            repo = hub.get_repo(repo_id)
        return Success(repo)
    except (GithubException, TimeoutException):
        return Failure(DownloadErrorCode.FETCH_ARCHIVE_FAILED)


RepoArchive = GitRelease | Tag | Commit


def fetch_archive(
    repo: Repository,
) -> Result[tuple[RepoArchive, str], DownloadErrorCode]:
    """fetch the archive of a repo
    try: latest release -> latest tag -> latest commit

    Returns: (archive, its tarball url)
    """
    # try latest release
    try:
        latest_release = repo.get_latest_release()
        return Success((latest_release, latest_release.tarball_url))
    except GithubException:
        pass

    # try latest tag
    try:
        tags = repo.get_tags()
        if tags.totalCount > 0:
            latest_tag: Tag = next(iter(tags))
            return Success((latest_tag, latest_tag.tarball_url))
    except GithubException:
        pass

    # try latest commit
    try:
        commit = next(iter(repo.get_commits()))
        tarball_url = f"https://api.github.com/repos/{repo.owner.login}/{repo.name}/tarball/{commit.sha}"
        return Success((commit, tarball_url))
    except GithubException:
        return Failure(DownloadErrorCode.FETCH_ARCHIVE_FAILED)


def download_archive(
    path: str, url: str, timeout: int
) -> Result[None, DownloadErrorCode]:
    """download file from url to path with timeout limit"""
    try:
        with time_limit(timeout):
            resp = requests.get(url, timeout=None)  # use self-defined time_limit
            resp.raise_for_status()
    except (TimeoutError, TimeoutException):
        return Failure(DownloadErrorCode.DOWNLOAD_ARCHIVE_FAILED)

    with open(path, "wb") as outfile:
        outfile.write(resp.content)

    return Success(None)


def download_repo(
    hub: Github, repo_id: str, path: str, fetch_timeout: int, download_timeout: int
):

    def download_archive_to_path(p: tuple[RepoArchive, str]):
        _, url = p
        return download_archive(path, url, download_timeout).map(lambda _: p)

    return (
        fetch_repo(repo_id, timeout=fetch_timeout, hub=hub)
        .bind(fetch_archive)
        .bind(download_archive_to_path)
    )


def main(
    input_repo_list_path: str = "data/meta/oss_fuzz_python_filtered.txt",
    fetch_timeout: int = 30,
    download_timeout: int = 300,
    delay: Tuple[int, int] | int = -1,
    oroot: str = "data/repos/",
    log: Optional[str] = "download_log.jsonl",
    limits: int = -1,
    oauth: str = "oauth",
):
    if log:
        log = os.path.join(oroot, log)
    # declare github object
    # oauth is provided for rate limit:
    # https://docs.github.com/en/rest/overview/resources-in-the-rest-api?apiVersion=2022-11-28#rate-limiting
    # 5k calls per hours if authorized, otherwise, 60 calls or some
    hub: Github
    try:
        hub = Github(auth=Auth.Token(get_access_token(oauth)))
    except GithubException:
        hub = Github()
    # if repo_id_list is a file then load lines
    # otherwise it is the id of a specific repo
    with open(input_repo_list_path, "r") as fp:
        repo_id_list = [line.strip() for line in fp.readlines()]

    if limits >= 0:
        repo_id_list = repo_id_list[:limits]

    logging.info(f"Loaded {len(repo_id_list)} repos to be downloaded")
    failed = [0, 0, 0, 0]
    for repo_id in (pbar := tqdm(repo_id_list)):
        # log repo_id and rate limits
        rate = hub.get_rate_limit()
        pbar.set_description(
            f"Downloading {repo_id}, Rate: {rate.core.remaining}/{rate.core.limit}"
        )

        # download repo
        repo_path = os.path.join(oroot, wrap_repo(repo_id))
        tar_path = repo_path + ".tar.gz"
        match download_repo(hub, repo_id, tar_path, fetch_timeout, download_timeout):
            case Success((_, url)):
                try:
                    with tarfile.open(tar_path) as tp:
                        tp.extractall(repo_path)
                    log_or_skip(
                        log,
                        repo_id=repo_id,
                        archive=url,
                        download=tar_path,
                    )
                except tarfile.ReadError:
                    log_or_skip(
                        log,
                        repo_id=repo_id,
                        archive=url,
                        download=tar_path,
                        error_code=DownloadErrorCode.TARFILE_EXTRACT_FAILED,
                    )
                    failed[DownloadErrorCode.TARFILE_EXTRACT_FAILED] += 1
            case Failure(status):
                failed[status] += 1
                log_or_skip(log, repo_id=repo_id, error_code=status)
        # delay
        sleep_time = delay if isinstance(delay, int) else random.randint(*delay)
        if sleep_time > 0:
            time.sleep(sleep_time)

    if sum(failed):
        failed_types = ["repo", "archive", "download", "extract"]
        failed_dict = {key: val for key, val in zip(failed_types, failed) if val != 0}
        logging.warning(f"Failed: {failed_dict}")
    logging.info("Done!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
