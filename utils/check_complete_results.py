import os
import argparse
from pathlib import Path
from collections import defaultdict
import PyPDF2
 


def get_pdf_page_count(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            return len(pdf.pages)
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")
        return None


def collect_mmd_files(mmd_root):
    # dictionary to store paper_id -> list of page numbers
    mmd_files = defaultdict(list)
    
    # walk through all subdirectories
    for month_dir in os.listdir(mmd_root):
        month_path = os.path.join(mmd_root, month_dir)
        if not os.path.isdir(month_path):
            continue
            
        for filename in os.listdir(month_path):
            if not filename.endswith('.mmd'):
                continue
                
            # extract paper ID and page number - paper_id_page.mmd
            base_name = filename[:-4]  # remove .mmd
            paper_id, page_num = base_name.rsplit('_', 1)
            mmd_files[paper_id].append(int(page_num))
            
    return mmd_files

def main(args):
    pdf_root = Path(args.pdf_dir)
    mmd_root = Path(args.mmd_dir)
    
    complete = []
    incomplete = []
    missing = []
    
    # collect all MMD files first
    print("Collecting MMD files...")
    mmd_files = collect_mmd_files(mmd_root)
    
    # process each PDF file
    print("\nChecking PDFs against MMD files...")
    for month_dir in os.listdir(pdf_root):
        month_path = os.path.join(pdf_root, month_dir)
        if not os.path.isdir(month_path):
            continue
            
        for pdf_file in os.listdir(month_path):
            if not pdf_file.endswith('.pdf'):
                continue
                
            paper_id = pdf_file[:-4]  # remove .pdf extension
            pdf_path = os.path.join(month_path, pdf_file)
            
            # get PDF page count
            pdf_pages = get_pdf_page_count(pdf_path)
            if pdf_pages is None:
                print(f"Skipping {pdf_file} due to error")
                continue
            
            # check if we have MMD files for this paper
            if paper_id in mmd_files:
                mmd_pages = len(mmd_files[paper_id])
                max_page = max(mmd_files[paper_id])
                
                # check if all pages are present (no gaps)
                expected_pages = set(range(1, max_page + 1))
                actual_pages = set(mmd_files[paper_id])
                
                if mmd_pages == pdf_pages and expected_pages == actual_pages:
                    complete.append((paper_id, pdf_pages))
                else:
                    incomplete.append((paper_id, pdf_pages, mmd_pages))
                    if expected_pages != actual_pages:
                        missing_pages = sorted(expected_pages - actual_pages)
                        print(f"Paper {paper_id} has gaps: missing pages {missing_pages}")
            else:
                missing.append((paper_id, pdf_pages))
    
    # print summary
    print("\nSummary:")
    print(f"Complete conversions: {len(complete)}")
    print(f"Incomplete conversions: {len(incomplete)}")
    print(f"Missing conversions: {len(missing)}")
    
    # print details of incomplete conversions
    if incomplete:
        print("\nIncomplete conversions details:")
        for paper_id, pdf_pages, mmd_pages in incomplete:
            print(f"Paper {paper_id}: Expected {pdf_pages} pages, found {mmd_pages} MMD files")
    
    # print details of missing conversions
    if missing:
        print("\nMissing conversions details:")
        for paper_id, pdf_pages in missing:
            print(f"Paper {paper_id}: No MMD files found (PDF has {pdf_pages} pages)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check completeness of PDF to MMD conversion')
    parser.add_argument(
        '--pdf-dir', type=str, required=True, 
        help='Root directory containing PDF files organized by month'
    )
    parser.add_argument(
        '--mmd-dir', type=str, required=True,
        help='Root directory containing MMD files organized by month'
    )
    args =  parser.parse_args()
    main(args)