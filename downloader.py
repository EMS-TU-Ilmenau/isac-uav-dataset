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
import requests
import requests.exceptions
from tqdm.auto import tqdm

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Carsten Smeenk, Zhixiang Zhao"
__version__ = "0.5"
__license__ = "CC-BY-SA-4.0"
__maintainer__ = "Steffen Schieler"
__email__ = "steffen.schieler@tu-ilmenau.de"
__status__ = "Development"

SERVER = "https://ftp.tu-ilmenau.de"
DIR = "/hpc-private/ems1/test1/"
SHASUM_FILE = "scenarios.checksum"

class Downloader:
    @classmethod
    def download(cls, url: str, out_file: str):
        if not cls._check_if_server_is_available(SERVER):
            raise ConnectionError("Unable to connect to server!")
        
        logging.info(f"Connection to Server { SERVER } established.")

        if not cls._check_if_file_exists_on_server(url):
            raise FileNotFoundError("File not found on server!")
        
        logging.info(f"Found file under URL on `{ url }`.")

        if not cls._download_file_from_server(url, out_file=out_file):
            raise Exception(f"Failed to download file { url } from server.")

        return

    @staticmethod
    def _check_if_server_is_available(url: str) -> bool:
        try:
            r = requests.get(url)
            r.raise_for_status()
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logging.error("Server is unreachable!")
        except requests.exceptions.HTTPError:
            logging.error(f"Encountered HTTP-Errors 4xx or 5xx")
        
        return False

    @staticmethod
    def _check_if_file_exists_on_server(url: str) -> bool:
        file_head = requests.head(url)
        if file_head is not None:
            return True

        return False


    @staticmethod
    def _download_file_from_server(url: str, out_file: str) -> bool:
        response = requests.get(url, stream=True)  # Streaming, so we can show a progress bar.
        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024 #1 KiB
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc=f"Downloading { url }")
        with open(out_file, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        
        progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            logging.error("Something went wrong while downloading the file.")
            return False

        return True


def decrypt_file(in_file: str, password: str, out_file: str = None) -> bool:
    if out_file is None:
        out_file = in_file.split(".encrypted")[0]

    logging.info(f"Decrypting downloaded file {in_file} as {out_file}.")
    proc = subprocess.run(["openssl", "enc", "-d", "-aes256", "-pass", f"pass:{password}", "-in", in_file, "-out", out_file])

    return not(bool(proc.returncode))

def unpack_file(archive: str, out_dir: str, file_to_unpack: str) -> bool:
    logging.info(f"Unpacking file { file_to_unpack } from archive { archive } to { out_dir }.")
    with tarfile.open(archive, mode="r") as tf:
        # TODO: Uncomment the below
        # tf.extract(member=file_to_unpack, path=out_dir)
        # TODO: REMOVE THE BELOW
        tf.extract(member="some_crazy_measurement/some_crazy_measurement_file.h5", path=out_dir,)

    os.replace(os.path.join(os.getcwd(), "some_crazy_measurement/some_crazy_measurement_file.h5",), os.path.join(os.getcwd(), file_to_unpack))
    os.rmdir(os.path.join(os.getcwd(), "some_crazy_measurement"))
    # TODO: STOP REMOVE

    return

def check_shasum(shasum: dict, h5_file: str, dir: str) -> bool:
    logging.info(f"Checking Shasum-256 using Repos `*.checksum` files to verify downloaded Scenario { h5_file }.")
    hash_func = sha256()
    with open(h5_file, "rb") as f:
        for chunk in iter(lambda: f.read(2**23), b""):
            hash_func.update(chunk)

    hash = hash_func.hexdigest()
    if shasum != hash:
        logging.warn(f"The shasums of the downloaded file and in the Gitlab did not match!")
        return False

    logging.info(f"Shasum-256 of {h5_file} and Shasum-256 in Git repository matched!")   
    return True

def create_download_dir(dir: str) -> None:
    try: 
        os.mkdir(dir)
        logging.info(f"Temporary download directory created in `{ dir }`.")
    except FileExistsError:
        logging.info(f"Temporary download directory already exists.")

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

def main(args, shasums):
    repo_dir = args.output_dir
    tmp_dir = os.path.join(repo_dir, ".tmp")
    create_download_dir(tmp_dir)
    password = getpass("Please enter the password to decrypt the files:")

    for scenario in args.scenario:
        url = f"{SERVER}{ DIR }{scenario}.tar.bz2"
        # context manager deletes tmpdir when finished
        encrypted_file = os.path.join(tmp_dir ,f"{ scenario }.tar.bz2.encrypted")
        decrypted_file = os.path.join(tmp_dir, f"{ scenario }.tar.bz2")
        h5_filename = f"{ scenario }.h5"
        shasum = shasums[h5_filename]

        if not os.path.exists(encrypted_file) or args.overwrite:
            Downloader.download(url, out_file=encrypted_file)
        else:
            logging.info("Reusing previously downloaded file.")

        # decrypt file in tmpdir
        if not os.path.exists(decrypted_file):
            if not decrypt_file(in_file=encrypted_file, password=password, out_file=decrypted_file):
                raise Exception(f"Failed to decrypt file. Did you enter the correct password?")

        # unpack file from tmpdir to repodir
        if not os.path.exists(os.path.join(repo_dir, h5_filename)):
            unpack_file(archive=decrypted_file, out_dir=repo_dir, file_to_unpack= h5_filename)

        # check shasum of file with *.checksum file from repo
        if not args.no_shasum:
            check_shasum(shasum, h5_filename, repo_dir)
        else: 
            logging.warn(f"Skipping Shasum-check.")

        if not args.no_cleanup:
            os.remove(encrypted_file)
            os.remove(decrypted_file)
    
    if not args.no_cleanup:
        os.rmdir(tmp_dir)

    logging.info("All done. Exiting.")

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
        "-ns",
        "--no-shasum",
        help="Do not check whether the downloaded file is correct w.r.t. the Shasum defined in the Git repository. WARNING: Disabling is potentially dangerous!",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Re-download and overwrite previously downloaded files",
        action="store_true",
    )

    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()

    if not os.path.exists(args.shasum_file):
        raise FileNotFoundError(f"No shasum file found at path {args.shasum_file}. Use `--shasum-file` to specify a correct path.")

    shasums = load_shasum_dict(args.shasum_file)
    all_scenarios = [ x.split(".h5")[0] for x in shasums.keys()]

    if args.scenario is None:
        args.scenario = all_scenarios

    main(args, shasums)