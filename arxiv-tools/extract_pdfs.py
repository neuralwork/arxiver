#!/usr/bin/env python3
"""
arXiv Tar Extraction Script

Extracts PDF files from arXiv tar archives into organized directories.
The script processes tar files named like 'arXiv_pdf_YY_MM_N.tar' and organizes PDFs into
YYMM directories.

Usage:
    python extract_arxiv.py --data_dir /path/to/tar/files
"""

import os
import tarfile
import logging
import argparse
from typing import List
from pathlib import Path


def setup_logging() -> logging.Logger:
    """Configure and return logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("arxiv_extract.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("arxiv_extractor")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract PDFs from arXiv tar archives",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="Directory containing arXiv tar files"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="extracted",
        help="Base directory for extracted PDFs"
    )
    parser.add_argument(
        "--keep_tars",
        action="store_true",
        help="Keep tar files after extraction (default: delete)"
    )
    
    return parser.parse_args()


def get_tar_files(data_dir: Path) -> List[Path]:
    """
    Find all tar files in the specified directory.
    
    Args:
        data_dir: Directory to search for tar files
        
    Returns:
        List of paths to tar files
    """
    return list(data_dir.glob("*.tar"))


def extract_pdfs_from_tar(
    tar_path: Path,
    output_base: Path,
    keep_tar: bool = False
) -> bool:
    """
    Extract PDF files from a tar archive into a year-month directory.
    
    Args:
        tar_path: Path to the tar file
        output_base: Base directory for extracted files
        keep_tar: Whether to keep the tar file after extraction
        
    Returns:
        bool: True if extraction successful, False otherwise
    """
    logger = logging.getLogger("arxiv_extractor")
    
    try:
        # extract directory name (YYMM) from tar file name
        # example: "arXiv_pdf_23_10_1.tar" -> "2310"
        parts = tar_path.stem.split("_")
        if len(parts) != 5 or not parts[2].isdigit() or not parts[3].isdigit():
            logger.warning("Invalid tar file name format: %s", tar_path.name)
            return False
            
        dir_name = parts[2] + parts[3]  # e.g., "2310" for year 23, month 10
        output_dir = output_base / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Extracting %s to directory %s", tar_path.name, output_dir)
        
        # Extract PDF files
        with tarfile.open(tar_path, "r") as tar:
            pdf_members = [m for m in tar.getmembers() 
                         if m.isreg() and m.name.endswith(".pdf")]
            
            total_pdfs = len(pdf_members)
            for i, member in enumerate(pdf_members, 1):
                tar.extract(member, output_dir)
                if i % 100 == 0:  # log progress every 100 files
                    logger.info("Extracted %d/%d PDFs (%.1f%%)",
                              i, total_pdfs, (i/total_pdfs)*100)
            
            logger.info("Successfully extracted %d PDF files to %s",
                       total_pdfs, output_dir)
        
        # clean up tar file if requested
        if not keep_tar:
            tar_path.unlink()
            logger.info("Deleted tar file: %s", tar_path.name)
        
        return True
        
    except Exception as e:
        logger.error("Error processing %s: %s", tar_path.name, str(e))
        return False


def main():
    args = parse_args()
    logger = setup_logging()
    
    data_dir = Path(args.data_dir)
    output_base = Path(args.output_dir)
    
    if not data_dir.is_dir():
        logger.error("Data directory does not exist: %s", data_dir)
        return
    
    # create output base directory
    output_base.mkdir(parents=True, exist_ok=True)
    
    # get list of tar files
    tar_files = get_tar_files(data_dir)
    if not tar_files:
        logger.error("No tar files found in %s", data_dir)
        return
    
    logger.info("Found %d tar files to process", len(tar_files))
    
    # process each tar file
    successful = 0
    failed = 0
    
    for tar_path in tar_files:
        if extract_pdfs_from_tar(tar_path, output_base, args.keep_tars):
            successful += 1
        else:
            failed += 1
    
    # log final statistics
    logger.info("\nExtraction complete:")
    logger.info("- Successful: %d", successful)
    logger.info("- Failed: %d", failed)
    logger.info("- Total processed: %d", len(tar_files))


if __name__ == "__main__":
    main()



