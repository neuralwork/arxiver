import os
import csv
import time
import requests
import argparse
from pathlib import Path

from tqdm import tqdm
import xml.etree.ElementTree as ET



def get_arxiv_metadata(arxiv_id):
    """Fetch metadata for a single arxiv paper."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        # parse the XML response
        root = ET.fromstring(response.content)
        ns = {"http://www.w3.org/2005/Atom"}
        
        entry = root.find("atom:entry", ns)
        if entry:
            title = entry.find("atom:title", ns).text.strip()
            abstract = entry.find("atom:summary", ns).text.strip()
            authors = [author.find("atom:name", ns).text for author in entry.findall("atom:author", ns)]
            published_date = entry.find("atom:published", ns).text.strip()
            link = entry.find("atom:link", ns).get("href")
            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published_date": published_date,
                "link": link
            }
    return None


def process_mmd_files(input_dir: Path):
    """Process MMD files and extract metadata."""
    # ensure output file exists with headers
    with open("arxiv_metadata.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "title", "abstract", "authors", "published_date", "link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    # collect all mmd files from input directory including subdirectories
    mmd_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".mmd"):
                mmd_files.append(os.path.join(root, file))
    mmd_files.sort()

    # process files
    for mmd_path in tqdm(mmd_files, desc="Processing MMD files"):
        arxiv_id = Path(mmd_path).stem  # get filename without extension
        
        metadata = get_arxiv_metadata(arxiv_id)
        if metadata:
            # append to csv
            with open("arxiv_metadata.csv", "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    "id": arxiv_id,
                    "title": metadata["title"],
                    "abstract": metadata["abstract"],
                    "authors": ", ".join(metadata["authors"]),
                    "published_date": metadata["published_date"],
                    "link": metadata["link"]
                })
        
        # respect arXiv API rate limits (3 requests per second)
        time.sleep(3)


def main(args):
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    print("Starting metadata extraction...")
    start_time = time.time()
    
    process_mmd_files(input_dir)
    
    processing_time = time.time() - start_time
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print("Results saved to: arxiv_metadata.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract metadata from arXiv papers using their IDs"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Input directory containing MMD files (can include subdirectories)"
    )
    args = parser.parse_args()
    main(args)