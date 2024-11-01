"""
!/usr/bin/env python3
Nougat batch inference script

Processes PDFs with Nougat model in batches and extracts text to multi markdown files.
Works with a directory structure organized by year-month (YYMM).

Usage:
    python nougat_inference.py --input_dir /path/to/pdfs --output_dir /path/to/output --gpu_id 0
"""

import time
import logging
import argparse
from functools import partial
from pathlib import Path
from typing import List

import torch
import pypdf
from tqdm import tqdm
from nougat import NougatModel
from nougat.utils.dataset import LazyDataset
from nougat.utils.checkpoint import get_checkpoint
from nougat.postprocessing import markdown_compatible


def setup_logging(output_dir: Path) -> None:
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(output_dir / "nougat_inference.log"),
            logging.StreamHandler()
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process PDFs with Nougat model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing PDF files organized in YYMM folders"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory for output markdown files"
    )
    parser.add_argument(
        "--gpu_id",
        type=int,
        default=0,
        help="GPU ID to use for inference"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="Batch size for processing pages"
    )
    return parser.parse_args()


def load_model_to_gpu(model_tag: str, gpu_id: int) -> NougatModel:
    """Initialize and load Nougat model to specified GPU."""
    logger = logging.getLogger("nougat_inference")
    logger.info(f"Loading model {model_tag} to GPU {gpu_id}")
    checkpoint = get_checkpoint(None, model_tag=model_tag)
    model = NougatModel.from_pretrained(checkpoint)
    model.to(f"cuda:{gpu_id}").to(torch.bfloat16)
    model.eval()
    return model


def get_pdf_files(input_dir: Path) -> List[Path]:
    """Get all PDF files from the input directory structure."""
    pdf_files = []
    for month_dir in input_dir.iterdir():
        if month_dir.is_dir():
            pdf_files.extend(month_dir.glob("*.pdf"))
    return sorted(pdf_files)


def process_pdf(pdf_path: Path, output_dir: Path, model: NougatModel, batch_size: int) -> bool:
    """
    Process all pages of a PDF document with the Nougat model.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory for output files
        model: Loaded Nougat model
        batch_size: Number of pages to process at once
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger = logging.getLogger("nougat_inference")
    start_time = time.time()
    
    # get document ID (remove .pdf and use full path structure)
    document_id = pdf_path.stem
    month_dir = pdf_path.parent.name

    try:
        # prepare dataset for all pages
        full_dataset = LazyDataset(
            str(pdf_path), partial(model.encoder.prepare_input, random_padding=False)
        )
    except pypdf.errors.PdfStreamError as e:
        logger.error(f"Failed to load PDF {document_id}: {str(e)}")
        return False

    # create dataloader
    dataloader = torch.utils.data.DataLoader(
        full_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=LazyDataset.ignore_none_collate,
    )
    
    try:
        # create month directory in output
        month_output_dir = output_dir / month_dir
        month_output_dir.mkdir(exist_ok=True)
        
        # process pages
        for batch_idx, (sample, is_last_page) in enumerate(tqdm(dataloader, desc=f"Processing {document_id}")):
            with torch.no_grad():
                model_output = model.inference(
                    image_tensors=sample,
                    early_stopping=False
                )

            # save predictions for each page
            for j, output in enumerate(model_output["predictions"]):
                page_num = batch_idx * batch_size + j + 1
                formatted_output = markdown_compatible(output.strip())
                
                output_path = month_output_dir / f"{document_id}_{page_num}.mmd"
                output_path.write_text(formatted_output)

        elapsed_time = time.time() - start_time
        logger.info(f"Processed {document_id} in {elapsed_time:.2f} seconds")
        return True

    except Exception as e:
        logger.error(f"Error processing {document_id}: {str(e)}")
        return False


def main():
    """Main execution function."""
    args = parse_args()
    
    # create output directory and setup logging
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(output_dir)
    logger = logging.getLogger("nougat_inference")
    
    # load Nougat model
    model = load_model_to_gpu("0.1.0-small", args.gpu_id)
    
    # get PDF files
    pdf_files = get_pdf_files(input_dir)
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # process PDFs
    processed = 0
    failed = 0
    
    for pdf_path in tqdm(pdf_files, desc="Overall progress"):
        if process_pdf(pdf_path, output_dir, model, args.batch_size):
            processed += 1
        else:
            failed += 1
    
    # log final summary
    logger.info("\nProcessing Summary:")
    logger.info(f"Successfully processed: {processed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total files attempted: {processed + failed}")


if __name__ == "__main__":
    main()