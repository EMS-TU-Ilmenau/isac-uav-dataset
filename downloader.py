import argparse
from tkinter import N
from tqdm.auto import tqdm
import requests
import requests.exceptions
import tempfile
import os
import subprocess
import logging
import pdb

SERVER = "https://ftp.tu-ilmenau.de"
DIR = "/hpc-private/ems1/test1/"
SCENARIOS = [
    "droneshield_h15_v11_1to2",
]

def check_if_server_is_available(url: str) -> bool:
    try:
        r = requests.get(url)
        r.raise_for_status()
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logging.error("Server is unreachable!")
    except requests.exceptions.HTTPError:
        logging.error(f"Encountered HTTP-Errors 4xx or 5xx")
    
    return False

def check_if_file_exists_on_server(url: str) -> bool:
    file_head = requests.head(url)
    if file_head is not None:
        return True

    return False

def download_file_from_server(url: str, out_file: str) -> bool:
    response = requests.get(url, stream=True)  # Streaming, so we can iterate over the response.
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
    proc = subprocess.run(["openssl", "enc", "-d", "-aes256", "-in", in_file, "-out", out_file])

    return not(bool(proc.returncode))

def unpack_file(out_dir: str, file: str) -> bool:
    logging.info(f"Unpacking archive { file } to { out_dir }.")
    proc = subprocess.run(["tar", "--extract", "--bzip2", "--strip-components", "1", "--verbose", "--directory", out_dir, "--file", file])

    return not(bool(proc.returncode))

def check_shasum(dir: str) -> bool:
    logging.info(f"Checking Shasum using Repos `*.checksum` files to verify download.")
    proc = subprocess.run(["shasum", "--check", "scenarios.checksum"], cwd=dir)

    return not(bool(proc.returncode))

def main(args):
    for scenario in args.scenario:
        url = f"{SERVER}{ DIR }{scenario}.tar.bz2"
        repo_dir = os.getcwd()

        if not check_if_server_is_available(SERVER):
            raise ConnectionError("Unable to connect to server!")
        
        logging.info(f"Connection to Server { SERVER } established.")

        if not check_if_file_exists_on_server(url):
            raise FileNotFoundError("File not found on server!")
        
        logging.info(f"Found file under URL on `{ url }`.")

        # context manager deletes tmpdir when finished
        with tempfile.TemporaryDirectory() as tmpdir:
            encrypted_file = os.path.join(tmpdir, f"{ scenario }.tar.bz2.encrypted")
            decrypted_file = os.path.join(tmpdir, f"{ scenario }.tar.bz2")

            # download file to tmpdir
            if not download_file_from_server(url, out_file=encrypted_file):
                raise Exception(f"Failed to download file { url } from server. This indicates network issues.")

            # decrypt file in tmpdir
            if not decrypt_file(in_file=encrypted_file, out_file=decrypted_file):
                raise Exception(f"Failed to decrypt file. Did you enter the correct password?")

            # unpack file from tmpdir to repodir
            if not unpack_file(out_dir=repo_dir, file=decrypted_file):
                raise Exception(f"Failed to unpack the file for unspecific reasons. Re-run script or try manually with `tar --extract --bzip2 --verbose --directory <out_dir> --file { scenario }`.")

    # check shasum of file with *.checksum file from repo
    if not check_shasum(dir=repo_dir):
        raise Exception(f"Shasum did not match! The file does not correspond to the one specified in the Git repository.")
    


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
        default=SCENARIOS,
    )
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    main(args)