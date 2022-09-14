import argparse
from tkinter import N
from tqdm.auto import tqdm
import requests
import requests.exceptions
import os
import subprocess
import logging

SERVER = "https://ftp.tu-ilmenau.de"
DIR = "/hpc-private/ems1/test1/"
FILE = "droneshield_h15_v11_1to2.tar.bz2"

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
    # do smth with it to verify it is correct
    if file_head is not None:
        return True

    return False

def download_file_from_server(url: str, out_file: str):
    response = requests.get(url, stream=True)  # Streaming, so we can iterate over the response.
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 KiB
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc=f"Downloading { FILE }")
    with open(f"{out_file}.encrypted", 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        logging.error("Something went wrong while downloading the file.")    

    return

def decrypt_file(in_file: str, out_file: str = None):
    if out_file is None:
        out_file = in_file.split(".encrypted")[0]

    logging.info(f"Decrypting downloaded file {in_file} as {out_file}.")
    subprocess.run(["openssl", "enc", "-d", "-aes256", "-in", in_file, "-out", out_file])
    print("\n")
    return

def unpack_file(out_dir: str, file: str):
    logging.info(f"Unpacking archive { file } to { out_dir }.")
    subprocess.run(["tar", "--extract", "--bzip2", "--verbose", "--directory", out_dir, "--file", file])
    print("\n")
    return

def check_shasum(dir: str, checksum_file: str):
    logging.info(f"Checking Shasum of file { checksum_file.split('.checksum')[0] } to verify download.")
    subprocess.run(["shasum", "--check", checksum_file], cwd=dir)
    print("\n")
    return 


def main(args):
    url = f"{SERVER}{ DIR }{ FILE }"

    if not check_if_server_is_available(SERVER):
        raise ConnectionError("Unable to connect to server!")
    
    logging.info(f"Connection to Server { SERVER } established.")

    if not check_if_file_exists_on_server(url):
        raise FileNotFoundError("File not found on server!")
    
    logging.info(f"Found file { FILE } on { SERVER }.")

    download_file_from_server(url, out_file=f"./{ FILE }")
    decrypt_file(in_file=f"{FILE}.encrypted", out_file=FILE)
    unpack_file(out_dir="./unpacked", file=FILE)
    check_shasum(dir="./unpacked/some_crazy_measurement/", checksum_file="some_crazy_measurement_file.checksum")

    logging.info("All done. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Downloader for the Measurement files."
    )
    parser.add_argument(
        "-s",
        "--scenario",
        help="The scenario to download. Must be a valid scenario string from the 2021 measurement."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Specify the output directory for the downloaded files. Default is $cwd.",
        nargs="?",
        default=os.getcwd(),
    )
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    main(args)