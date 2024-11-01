import os
import logging
import subprocess
from argparse import ArgumentParser
import xml.etree.ElementTree as ET


# set up logging configuration
log_file = os.path.join("logs", "preprocessing_logs.log")
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler() 
    ]
)
logger = logging.getLogger(__name__)

def download_files(**args):
    manifest_file = args["manifest_file"]
    mode = args["mode"]
    out_dir = args["output_dir"]

    if mode != "pdf" and mode != "src":
        logger.error("Invalid mode: %s. Mode should be 'pdf' or 'src'.", mode)

    def get_file(fname, out_dir):
        cmd = ["s3cmd", "get", "--requester-pays", "s3://arxiv/%s" % fname, "./%s" % out_dir]
        logger.info("Downloading file: %s to %s", fname, out_dir)
        subprocess.call(' '.join(cmd), shell=True)

    try:
        for file in ET.parse(manifest_file).getroot().findall("file")[:1]:
            filename = file.find("filename").text
            logger.info("Processing file: %s", filename)

            get_file(filename, out_dir='%s/%s/' % (out_dir, mode))
            logger.debug("Successfully downloaded: %s", filename)
    except Exception as e:
        logger.error("Failed to process manifest file: %s", str(e), exc_info=True)

    logger.info("Download process completed")


if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("--manifest_file", "-m", type=str, help="The manifest file to download files from arXiv.", required=True)
    argparser.add_argument("--output_dir", "-o", type=str, default="data", help="Output directory to save files to.")
    argparser.add_argument("--mode", type=str, default="src", choices=set(("pdf", "src")), help="Can be 'pdf' or 'src'.")
    args = argparser.parse_args()
    download_files(**vars(args))
