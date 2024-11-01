# arXiv-tools

A tool for downloading and managing arXiv documents in bulk using Amazon S3.

## Prerequisites

- [Amazon AWS Account](https://aws.amazon.com/free) - required for accessing arXiv's bulk data on [Amazon S3](https://aws.amazon.com/s3)
- Python 2.x to use the `s3cmd` package
- Python 3.x for manifest file analysis

## Installation

1. Install s3cmd, a command-line tool for interacting with Amazon S3:
   ```bash
   pip install s3cmd  # Python 2 only
   ```

2. Configure s3cmd with your AWS credentials:
   ```bash
   s3cmd --configure
   ```
   > Note: You'll need your AWS credentials from the Account Management tab on the AWS website.

3. Install required Python packages for manifest file analysis:
   ```bash
   pip install pandas  # For Python 3.x
   ```

## Usage

### 1. Download Manifest Files

First, download the manifest files containing the complete list of available arXiv files:

**For PDF documents:**
```bash
s3cmd get --requester-pays \
    s3://arxiv/pdf/arXiv_pdf_manifest.xml \
    local-directory/arXiv_pdf_manifest.xml
```

**For source documents:**
```bash
s3cmd get --requester-pays \
    s3://arxiv/src/arXiv_src_manifest.xml \
    local-directory/arXiv_src_manifest.xml
```

### 2. Analyze Manifest Files (Optional)

Use the `eda_manifest.py` script to analyze the manifest files:

```bash
python eda_manifest.py
```

This script provides useful statistics about the arXiv dataset:
- Total size of the dataset in bytes, MB, and GB
- Total number of articles
- Average file sizes
- Number of files per time period
- Detailed statistics for recent years (2022-2023)

### 3. Download arXiv Files

Use the `download.py` script to fetch the actual files:

**For PDF files:**
```bash
python download.py \
    --manifest_file /path/to/pdf-manifest \
    --mode pdf \
    --output_dir /path/to/output
```

**For source files:**
```bash
python download.py \
    --manifest_file /path/to/src-manifest \
    --mode src \
    --output_dir /path/to/output
```

The files will be downloaded to your specified output directory. Each file is in `.tar` format and approximately 500MB in size.

### 4. Extract PDFs from Tar Files

After downloading the tar files, use `extract_pdfs.py` to extract PDFs into organized directories:

```bash
python extract_pdfs.py \
    --data_dir /path/to/tar/files \
    --output_dir /path/to/output \
    [--keep_tars]  # Optional: keep original tar files
```

The script will create and extract pdf files to year-month subdirectories (e.g., "2310" for October 2023). Example output structure:
```
output_dir/
    2310/           # October 2023
        paper1.pdf
        paper2.pdf
    2311/           # November 2023
        paper3.pdf
        paper4.pdf
```


## Additional Resources
- For metadata downloads, consider using [metha](https://github.com/miku/metha)

## Notes
- The arXiv files are stored in requester-pays buckets on Amazon S3
- Each archive file is approximately 500MB in size and uses the `.tar` format