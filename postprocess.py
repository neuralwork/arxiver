import os
import json
import time
import argparse
from pathlib import Path
from typing import Set, List, Tuple


def read_mmd(file_path: str) -> str:
    """Read MMD file content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_filename(filename: str) -> Tuple[str, str]:
    """Extract article ID and page number from filename."""
    base_name = filename[:-4] if filename.endswith(".mmd") else filename
    paper_id, page_num = base_name.rsplit("_", 1)
    return paper_id, page_num


def detect_headers(mmd: str) -> List[Tuple[int, str]]:
    """Detect headers in MMD content."""
    return [(i, line) for i, line in enumerate(mmd.splitlines()) if line.startswith("#")]


def has_abstract(mmd: str) -> bool:
    """Check if MMD content contains an abstract."""
    return any("abstract" in line.lower() for line in mmd.splitlines())


def find_references(mmd: str) -> bool:
    """Find references section in MMD content."""
    for line in mmd.splitlines():
        if line.startswith("#") and "references" in line.lower():
            return True
    return False


def remove_authors(mmd: str) -> str:
    """Remove author names while preserving layout."""
    lines = mmd.splitlines()
    abstract_line = 0
    for i, line in enumerate(lines):
        if line.startswith("#") and "abstract" in line.lower():
            abstract_line = i
            break
    return "\n".join([lines[0], ""] + lines[abstract_line:])


def remove_references(mmd: str) -> str:
    """Remove content after references section."""
    lines = mmd.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#") and "references" in line.lower():
            return '\n'.join(lines[:i])
    return mmd

class ArticleProcessor:
    def __init__(self):
        self.headers_detected = set()
        self.abstract_detected = set()
        self.reference_pages = {}
        self.article_pages = {}
        # track which month directory each article belongs to
        self.article_months = {}

    def process_month_directory(self, month_dir: Path):
        """Process all MMD files in a month directory."""
        if not month_dir.is_dir():
            return

        month_name = month_dir.name
        for mmd_path in month_dir.glob("*.mmd"):
            paper_id, page_num = parse_filename(mmd_path.name)
            
            # store month information
            self.article_months[paper_id] = month_name
            
            # store page information
            if paper_id not in self.article_pages:
                self.article_pages[paper_id] = []
            self.article_pages[paper_id].append(page_num)
            
            try:
                mmd_content = read_mmd(str(mmd_path))
                
                # only process first page for headers and abstract
                if page_num == '1':
                    if has_abstract(mmd_content):
                        self.abstract_detected.add(paper_id)
                    if len(detect_headers(mmd_content)) > 1:
                        self.headers_detected.add(paper_id)
                
                # check for references
                if find_references(mmd_content):
                    self.reference_pages[paper_id] = page_num
                    
            except Exception as e:
                print(f"Error processing {mmd_path}: {e}")

    def get_valid_articles(self) -> Set[str]:
        """Return articles with both headers and abstract."""
        return self.headers_detected.intersection(self.abstract_detected)

def postprocess_articles(input_dir: Path, output_dir: Path, processor: ArticleProcessor):
    """Postprocess articles by removing authors and references."""
    valid_articles = processor.get_valid_articles()
    
    for article_id in valid_articles:
        if article_id not in processor.reference_pages or article_id not in processor.article_pages:
            continue
            
        # get the year-month directory for this article
        month = processor.article_months[article_id]
        month_output_dir = output_dir / month
        month_output_dir.mkdir(parents=True, exist_ok=True)
        
        pages = sorted([int(p) for p in processor.article_pages[article_id]])
        ref_page = int(processor.reference_pages[article_id])
        processed_content = []
        
        for page_num in pages:
            mmd_path = input_dir / month / f"{article_id}_{page_num}.mmd"
            if not mmd_path.exists():
                continue
                
            content = read_mmd(str(mmd_path))
            
            if page_num == 1:
                content = remove_authors(content)
            elif page_num == ref_page:
                if not content.splitlines()[0].lower().startswith("# reference"):
                    content = remove_references(content)
                else:
                    continue
            elif page_num > ref_page:
                continue
                
            processed_content.append(content)
        
        if processed_content:
            output_path = month_output_dir / f"{article_id}.mmd"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write('\n'.join(processed_content))

def main(args):
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    print("Processing MMD files...")
    start_time = time.time()
    
    # initialize processor
    processor = ArticleProcessor()
    
    # process each month directory
    for month_dir in input_dir.iterdir():
        if month_dir.is_dir():
            print(f"Processing directory: {month_dir.name}")
            processor.process_month_directory(month_dir)
    
    valid_articles = processor.get_valid_articles()
    
    print(f"\nFound:")
    print(f"- Articles with headers and abstract: {len(valid_articles)}")
    print(f"- Articles with references: {len(processor.reference_pages)}")
    print(f"- Total articles: {len(processor.article_pages)}")
    
    # postprocess valid articles
    print("\nPostprocessing articles...")
    postprocess_articles(input_dir, output_dir, processor)
    
    processing_time = time.time() - start_time
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print(f"Processed files saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process arXiv MMD files: detect headers, abstracts, references, and postprocess"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Input directory containing MMD files organized by month (YYMM)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for processed MMD files (will maintain month structure)"
    )
    args = parser.parse_args()
    main(args)