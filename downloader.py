import argparse
from tqdm.auto import tqdm
import requests
import requests.exceptions
import tempfile
import tarfile
import os
import shutil
import subprocess
import pdb
import logging

SERVER = "https://ftp.tu-ilmenau.de"
DIR = "/hpc-private/ems1/test1/"
SHASUM_FILE = "scenarios.checksum"
LOCAL_DL_DIR = ".tmp"

class Downloader:
    @classmethod
    def download(cls, url: str, out_file: str, overwrite: bool = False):
        if cls._check_if_already_downloaded(out_file):
            if not overwrite:
                logging.info(f"Reusing previously downloaded file { out_file }.")
        else:
            cls._download_scenario(url, out_file)

        return
    
    @classmethod
    def _download_scenario(cls, url: str, out_file: str) -> None:
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
    def _check_if_already_downloaded(file: str) -> bool:
        return os.path.exists(file)

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

def decrypt_file(in_file: str, out_file: str = None) -> bool:
    if out_file is None:
        out_file = in_file.split(".encrypted")[0]

    logging.info(f"Decrypting downloaded file {in_file} as {out_file}.")
    # TODO: make an iteration for multiple user inputs
    proc = subprocess.run(["openssl", "enc", "-d", "-aes256", "-in", in_file, "-out", out_file])

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
    logging.info(f"Checking Shasum using Repos `*.checksum` files to verify downloaded Scenario { h5_file }.")
    proc = subprocess.run(["shasum", "--algorithm", "256", h5_file], cwd=dir, capture_output=True)
    if shasum != proc.stdout.decode("utf-8").split("  ")[0]:
        logging.warn(f"The shasums of the downloaded file and in the Gitlab did not match!")
        return False

    logging.info("Compared shasum matched!")
    
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
    repo_dir = os.getcwd()
    create_download_dir(dir=os.path.join(repo_dir, LOCAL_DL_DIR))

    for scenario in args.scenario:
        url = f"{SERVER}{ DIR }{scenario}.tar.bz2"
        # context manager deletes tmpdir when finished
        with tempfile.TemporaryDirectory() as tmpdir:
            encrypted_file = os.path.join(repo_dir, LOCAL_DL_DIR ,f"{ scenario }.tar.bz2.encrypted")
            decrypted_file = os.path.join(tmpdir, f"{ scenario }.tar.bz2")
            h5_filename = f"{ scenario }.h5"
            shasum = shasums[h5_filename]

            Downloader.download(url, out_file=encrypted_file, overwrite=args.overwrite)

            # decrypt file in tmpdir
            if not decrypt_file(in_file=encrypted_file, out_file=decrypted_file):
                raise Exception(f"Failed to decrypt file. Did you enter the correct password?")

            # unpack file from tmpdir to repodir
            unpack_file(archive=decrypted_file, out_dir=repo_dir, file_to_unpack= h5_filename)

            # check shasum of file with *.checksum file from repo
            if not args.no_shasum:
                check_shasum(shasum, h5_filename, repo_dir)
            else: 
                logging.warn(f"Skipping Shasum-check.")

    if not args.no_cleanup:
        logging.info(f"Removing temporary download files.")
        shutil.rmtree(os.path.join(repo_dir, LOCAL_DL_DIR))
    
    logging.info("All done. Exiting.")

if __name__ == "__main__":
    shasums = load_shasum_dict(os.path.join(os.getcwd(), SHASUM_FILE))
    scenarios = [ x.split(".h5")[0] for x in shasums.keys()]

    parser = argparse.ArgumentParser(
        description="Downloader for the Measurement files."
    )
    parser.add_argument(
        "-s",
        "--scenario",
        help=f"The list of scenarios to download, separated by spaces. If none is given, all scenarios are downloaded.",
        nargs="+",
        default=scenarios,
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
    main(args, shasums)