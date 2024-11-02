# Arxiver

A toolkit for downloading and converting arXiv papers to multi markdown (.mmd) format with Nougat - a neural OCR. Our pipeline can extract LaTeX equations and includes post-processing tools to clean up and merge extracted data. See the [arxiver](https://huggingface.co/datasets/neuralwork/arxiver) dataset on Hugging Face Hub for sample results.

## Project Structure
```
arxiver/
    arxiv-tools/          # Tools for downloading arXiv papers
    utils/                # Utility files to check processed data, get article metadata, etc.
    run_nougat.py         # Batch PDF processing script to extract text in .mmd format
    job_status_server.py  # Web server to monitor extraction progress
    postprocess.py        # Post-processing scripting to clean and merge Nougat outputs
```

## Downloading arXiv

The `arxiv-tools` folder contains scripts for downloading arXiv papers and computing useful statistics about the arXiv dataset. For detailed instructions, see the [arxiv-tools README](arxiv-tools/README.md). Downloading and extracting the dataset creates a hierarchical folder structure organized by publication year and month as follows:

```
output_dir/
    2310/           # October 2023
        paper1.pdf
        paper2.pdf
    2311/           # November 2023
        paper3.pdf
        paper4.pdf
```

## Nougat Processing

The `run_nougat.py` script processes PDF files in batches using the [Nougat](https://arxiv.org/abs/2308.13418) neural OCR model:

```bash
python run_nougat.py \
    --input_dir /path/to/datadir \
    --output_dir /path/to/output \
    --gpu_id 0 \
    --batch_size 8
```

You can run Nougat using the output data directory as an input argument. Running this script processes pdfs by batches on specified GPU and logs successful and failed jobs (Nougat is not 100% stable). Output structure maintains the same year-month-based subdirectory structure but saves each page separately:
```
output_dir/
    2310/
        paper1_1.mmd    # Paper 1, page 1
        paper1_2.mmd    # Paper 1, page 2
        paper2_1.mmd
    2311/
        paper3_1.mmd
        paper3_2.mmd
        paper4_1.mmd
```

#### Progress Monitoring
We provide an optinoal script, `job_status_server.py` to provide a web interface to monitor processing progress:

```bash
python job_status_server.py \
    --input_dir /path/to/pdf/files \
    --output_dir /path/to/output \
    --port 8005
```


## Post-Processing
The post-processing pipeline includes several steps to validate and clean up the Nougat output. You can optionally check how many of the papers have been fully processed (all pages successfully extracted) by running:
```bash
cd utils
python check_complete_results.py --pdf-dir /path/to/pdf/root/dir --mmd-dir /path/to/mmd/root/dir
```

You can use the output .mmd files as they are or run post-processing to remove headers and references and merge multiple page MMD files into single documents operations. To do this, run the post-processing script:
```bash
cd ..
python postprocess.py --input-dir /path/to/processed-data --output-dir /path/to/output
```

Note that this script preserves the original hierarchical folder structure organized by publication year and month.

#### Metadata Extraction
You can optionally get article metadata by running:
```bash
cd utils
python extract_metadata.py --input-dir /path/to/merged-mmd-folder
```

## Notes
- GPU with CUDA support is required for efficient processing
- Tested on an NVIDIA T4 GPU, processing speed depends on GPU memory and batch size
- arxiv-tools/ is adapted from the original [repo](https://github.com/armancohan/arxiv-tools)

From [neuralwork](https://neuralwork.ai/) with :heart:
