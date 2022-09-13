import argparse
from ipaddress import ip_address, IPv4Address
from tqdm.auto import tqdm
import requests
import requests.exceptions
import os
import logging

SERVER = ip_address("141.24.xxx.xxx")

def check_if_server_is_available(address: IPv4Address) -> bool:
    try:
        r = requests.get(address)
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logging.error("Server is unreachable!")
    except requests.exceptions.HTTPError:
        logging.error(f"Encountered HTTP-Errors 4xx or 5xx")
    else:
        return True
    
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
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(out_file, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        logging.error("Something went wrong while downloading the file.")    

    return


def main(args):
    url = f"some_subfolder/{ args.scenario }.tar.gz"

    if not check_if_server_is_available(SERVER):
        logging.error("Server is not available!")

    if not check_if_file_exists_on_server(url):
        logging.error("File is not available!")
    
    download_file_from_server(url)


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

    args = parser.parse_args()
    main(args)