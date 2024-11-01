"""
!/usr/bin/env python3
Job Status Server

A FastAPI server that monitors and reports Nougat inference progress.
Scans directories of MMD files to track processing progress.

Dependencies:
    - fastapi
    - uvicorn[standard]

Usage:
    python job_status_server.py
"""

import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Monitor Nougat inference progress",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing source PDF files"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory containing output MMD files"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8005,
        help="Port number for the server"
    )
    return parser.parse_args()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("job_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("job_status_server")

# initialize FastAPI app
app = FastAPI(
    title="Nougat Job Status Server",
    description="Monitor Nougat inference progress",
    version="1.0.0"
)

input_dir: Path = None
output_dir: Path = None
start_time: datetime = None


def calculate_time_difference(start: datetime, end: datetime) -> str:
    """Calculate and format the time difference between two timestamps."""
    time_difference = abs(end - start)
    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return f"{days} days, {hours} hours, and {minutes} minutes"


def count_pdf_files() -> int:
    """Count total number of PDF files in input directory."""
    total = 0
    for month_dir in input_dir.iterdir():
        if month_dir.is_dir():
            total += len(list(month_dir.glob("*.pdf")))
    return total


def get_processed_files() -> dict:
    """Get count of processed files per month directory."""
    processed = {}
    if output_dir.exists():
        for month_dir in output_dir.iterdir():
            if month_dir.is_dir():
                processed[month_dir.name] = len(list(month_dir.glob("*.mmd")))
    return processed


def get_job_stats() -> Tuple[int, int, float, dict]:
    """Calculate current job statistics."""
    try:
        total_pdfs = count_pdf_files()
        processed_files = get_processed_files()
        total_processed = sum(processed_files.values())
        remaining = total_pdfs - total_processed
        percentage = (total_processed / total_pdfs * 100) if total_pdfs > 0 else 0
        
        logger.info(
            "Stats - Total PDFs: %d, Processed: %d, Remaining: %d, Percentage: %.2f%%",
            total_pdfs, total_processed, remaining, percentage
        )
        
        return total_pdfs, total_processed, remaining, percentage, processed_files
    
    except Exception as e:
        logger.error("Error calculating job stats: %s", str(e))
        raise HTTPException(status_code=500, detail="Error calculating job statistics")


@app.get("/", response_class=HTMLResponse)
def status() -> HTMLResponse:
    """Generate HTML status page showing current job statistics."""
    try:
        total_pdfs, processed, remaining, percentage, processed_files = get_job_stats()
        elapsed_time = calculate_time_difference(start_time, datetime.now())
        
        # generate month-wise progress HTML
        month_progress = ""
        for month, count in sorted(processed_files.items()):
            month_progress += f"<p>Month {month}: {count:,} files processed</p>\n"
        
        return f"""
        <html>
            <head>
                <title>Nougat Inference Status</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                    }}
                    h1, h2 {{
                        color: #2c3e50;
                    }}
                    p {{
                        margin: 10px 0;
                    }}
                    .progress-bar {{
                        width: 100%;
                        background-color: #f0f0f0;
                        padding: 3px;
                        border-radius: 3px;
                        box-shadow: inset 0 1px 3px rgba(0, 0, 0, .2);
                    }}
                    .progress {{
                        width: {percentage}%;
                        height: 20px;
                        background-color: #4CAF50;
                        border-radius: 3px;
                    }}
                </style>
            </head>
            <body>
                <h1>Nougat Inference Progress</h1>
                <div class="progress-bar">
                    <div class="progress"></div>
                </div>
                <p>Total PDF files: {total_pdfs:,}</p>
                <p>Processed files: {processed:,}</p>
                <p>Remaining files: {remaining:,}</p>
                <p>Completion: {percentage:.2f}%</p>
                <p>Time elapsed: {elapsed_time}</p>
                
                <h2>Progress by Month</h2>
                {month_progress}
            </body>
        </html>
        """
    
    except Exception as e:
        logger.error("Error generating status page: %s", str(e))
        raise HTTPException(status_code=500, detail="Error generating status page")


@app.on_event("startup")
async def startup_event():
    """Initialize server state and log startup."""
    global start_time
    start_time = datetime.now()
    
    logger.info("Job Status Server starting up on port %d", args.port)
    logger.info("Monitoring input directory: %s", input_dir)
    logger.info("Monitoring output directory: %s", output_dir)
    total_pdfs = count_pdf_files()
    logger.info("Total PDF files to process: %d", total_pdfs)


if __name__ == "__main__":
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    uvicorn.run(app, host="0.0.0.0", port=args.port)