#!/usr/bin/env python3
"""Downloader for the Dataset files.

This script is used to download the actual dataset files, which are stored on a different server to keep the repository clean.
After being invoked, the script will perform the following tasks:
    - download the specified scenarios
    - decrypt the scenarios
    - unpack the archive
    - check the resulting file matches with the one specified in the repo (by comparing SHA256 hashes)

If a file was already downloaded, the script will not download it again, unless specified otherwise with the `--overwrite` argument (the same holds true for decryption and unpacking).
Call the script with `--help` to get a print of all supported arguments.
For most use-cases, running 
```bash
python downloader.py
```
is sufficient.

"""
import argparse
import os
import subprocess
import logging
from getpass import getpass
from hashlib import sha256
import tarfile
import urllib.request
from tqdm.auto import tqdm

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Carsten Smeenk, Zhixiang Zhao"
__version__ = "0.5"
__license__ = "CC-BY-SA-4.0"
__maintainer__ = "Steffen Schieler"
__email__ = "steffen.schieler@tu-ilmenau.de"
__status__ = "Development"

SERVER = "https://resdata.tu-ilmenau.de"
DIR = "/public/ei/ems/isac-uav-dataset/"
SHASUM_FILE = "scenarios.checksum"

RXS = ["VGH0", "VGH1", "VGH2"]

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    

class Downloader:
    @classmethod  
    def download(cls, url: str, out_file: str):
        if not cls._download_file_from_server(url, out_file=out_file):
            raise Exception(f"Failed to download file { url } from server.")

        return

    @classmethod
    def _download_file_from_server(cls, url: str, out_file: str) -> bool:
        class DownloadProgressBar(tqdm):
            def update_to(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)  
        
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
            urllib.request.urlretrieve(url, filename=out_file, reporthook=t.update_to)

        return True

def add_rx_to_scenarios(scenarios: list) -> list:
    allrx = []
    for scenario in scenarios:
        allrx.extend([f"{scenario}_{rx}" for rx in RXS])
        
    return allrx

def decrypt_file(in_file: str, password: str, out_file: str = None) -> bool:
    if out_file is None:
        out_file = in_file.split(".encrypted")[0]

    logger.info(f"Decrypting downloaded file {in_file} as {out_file}.")
    proc = subprocess.run(["openssl", "enc", "-d", "-aes256", "-pbkdf2", "-pass", f"pass:{password}", "-in", in_file, "-out", out_file])

    return not(bool(proc.returncode))

def unpack_file(archive: str, out_dir: str, file_to_unpack: str) -> bool:
    logger.info(f"Unpacking file { file_to_unpack } from archive { archive } to { out_dir }.")
    with tarfile.open(archive, mode="r") as tf:
        tf.extract(member=file_to_unpack, path=out_dir)

    return

def check_shasum(shasum: dict, h5_file: str, dir: str) -> bool:
    logger.info(f"Checking Shasum-256 using Repos `*.checksum` files to verify downloaded Scenario { h5_file }.")
    hash_func = sha256()
    with open(h5_file, "rb") as f:
        for chunk in iter(lambda: f.read(2**23), b""):
            hash_func.update(chunk)

    hash = hash_func.hexdigest()
    if shasum != hash:
        logger.warning(f"The shasums of the downloaded file and in the Gitlab did not match!")
        return False

    logger.info(f"Shasum-256 of {h5_file} and Shasum-256 in Git repository matched!")   
    return True

def create_download_dir(dir: str) -> None:
    try: 
        os.mkdir(dir)
        logger.info(f"Temporary download directory created in `{ dir }`.")
    except FileExistsError:
        logger.info(f"Temporary download directory already exists.")

    return

def load_shasum_dict(shasum_file: str) -> dict:
    shasums = {}
    with open(shasum_file) as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        for line in lines:
            value, key = line.split("  ")
            shasums[key] = value

    return shasums

def main(args, checksums):
    repo_dir = args.output_dir
    tmp_dir = os.path.join(repo_dir, ".tmp")
    create_download_dir(tmp_dir)
    password = getpass("Please enter the password to decrypt the files:")

    for scenario in args.scenario:
        url = f"{SERVER}{DIR}{scenario}.tar.bz2.encrypted"
        encrypted_file = os.path.join(tmp_dir ,f"{ scenario }.tar.bz2.encrypted")
        decrypted_file = os.path.join(tmp_dir, f"{ scenario }.tar.bz2")
        h5_filenames = [f"{ scenario }_{ type }.h5" for type in ["channel", "target"]]
        shasums = [checksums[x] for x in h5_filenames]

        if not os.path.exists(encrypted_file) or args.overwrite:
            Downloader.download(url, out_file=encrypted_file)
        else:
            logger.info("Reusing previously downloaded file.")

        # decrypt file in tmpdir
        if not os.path.exists(decrypted_file):
            if not decrypt_file(in_file=encrypted_file, password=password, out_file=decrypted_file):
                raise Exception(f"Failed to decrypt file. Did you enter the correct password?")

        # unpack file from tmpdir to repodir
        for h5_file in h5_filenames:
            if not os.path.exists(os.path.join(repo_dir, h5_file)):
                unpack_file(archive=decrypted_file, out_dir=repo_dir, file_to_unpack=h5_file)

        # check shasum of file with *.checksum file from repo
        for shasum, h5_file in zip(shasums, h5_filenames):
            check_shasum(shasum, h5_file, repo_dir)

        if not args.no_cleanup:
            os.remove(encrypted_file)
            os.remove(decrypted_file)

    logger.info("All done. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Downloader for the Measurement files."
    )
    parser.add_argument(
        "-s",
        "--scenario",
        help=f"The list of scenarios to download, separated by spaces. If none is given, all scenarios are downloaded.",
        nargs="+",
    )
    parser.add_argument(
        "--output-dir",
        help="Specify the output directory for the downloaded files. Default is the current working directory.",
        default=os.getcwd(),
    )
    parser.add_argument(
        "--shasum-file",
        help="Path to the `scenarios.checksum` file. Defaults to `$cwd/scenarios.checksum`.",
        default=os.path.join(os.getcwd(), "scenarios.checksum"),
    )    
    parser.add_argument(
        "-nc",
        "--no-cleanup",
        help="Do not delete temporary download files after succesful decryption and unpacking.",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Re-download and overwrite previously downloaded files",
        action="store_true",
    )

    logger = logging.getLogger("Data-Downloader")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())    
    args = parser.parse_args()
    
    # create console handler with a higher log level
    logger.addHandler(ch)

    if not os.path.exists(args.shasum_file):
        raise FileNotFoundError(f"No shasum file found at path {args.shasum_file}. Use `--shasum-file` to specify a correct path.")

    shasums = load_shasum_dict(args.shasum_file)
    all_scenarios = [ x.split("_channel.h5")[0] for x in shasums.keys() if "_channel.h5" in x]

    if args.scenario is None:
        args.scenario = all_scenarios
    else:
        args.scenario = add_rx_to_scenarios(args.scenario)

    main(args, shasums)
