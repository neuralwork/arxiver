"""
!/usr/bin/env python3
arXiv Manifest Analysis Script

This script analyzes XML manifest files from arXiv's bulk data access,
providing insights about file sizes, article counts, and temporal distribution.
"""

import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict


def parse_manifest(filepath: str) -> pd.DataFrame:
    """
    Parse the arXiv manifest XML file into a pandas DataFrame.
    
    Args:
        filepath: Path to the manifest XML file
        
    Returns:
        DataFrame containing parsed manifest data
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    data = [{
        "Filename": element.find("filename").text,
        "Number of Items": int(element.find("num_items").text),
        "Size": int(element.find("size").text),
        "Timestamp": element.find("timestamp").text,
        "YYMM": element.find("yymm").text,
    } for element in root.findall("file")]
    
    return pd.DataFrame(data)


def analyze_total_statistics(df: pd.DataFrame) -> Dict:
    """Calculate and return overall statistics from the manifest data."""
    total_size = df["Size"].sum()
    total_articles = df["Number of Items"].sum()
    total_tars = len(df)
    
    return {
        "total_size_bytes": total_size,
        "total_size_mb": total_size / 1e6,
        "total_size_gb": total_size / 1e9,
        "total_articles": total_articles,
        "total_tar_files": total_tars,
        "avg_article_size_mb": (total_size / total_articles) / 1e6,
        "avg_tar_size_mb": (total_size / total_tars) / 1e6,
        "avg_items_per_tar": total_articles / total_tars
    }


def analyze_yearly_data(df: pd.DataFrame, year: str) -> Dict:
    """
    Analyze manifest data for a specific year.
    
    Args:
        df: Full manifest DataFrame
        year: Two-digit year string (e.g., "22" for 2022)
        
    Returns:
        Dictionary containing year-specific statistics
    """
    year_df = df[df["YYMM"].str.startswith(year)]
    total_size = year_df["Size"].sum()
    total_articles = year_df["Number of Items"].sum()
    
    return {
        "total_articles": total_articles,
        "total_size_gb": total_size / 1e9,
        "data": year_df
    }


def print_statistics(stats: Dict) -> None:
    """Print formatted statistics."""
    print("\n=== Overall Statistics ===")
    print(f"Total Size: {stats['total_size_gb']:.2f} GB ({stats['total_size_bytes']:,} bytes)")
    print(f"Total Articles: {stats['total_articles']:,}")
    print(f"Total TAR Files: {stats['total_tar_files']:,}")
    print(f"\nAverages:")
    print(f"- Article Size: {stats['avg_article_size_mb']:.2f} MB")
    print(f"- TAR File Size: {stats['avg_tar_size_mb']:.2f} MB")
    print(f"- Items per TAR: {stats['avg_items_per_tar']:.1f}")


def main():
    # path to input manifest file
    MANIFEST_PATH = "arXiv_pdf_manifest.xml"
    
    # load and parse manifest
    print("Parsing manifest file...")
    df = parse_manifest(MANIFEST_PATH)
    
    # calculate overall statistics
    stats = analyze_total_statistics(df)
    print_statistics(stats)
    
    # analyze recent years
    print("\n=== Recent Years Analysis ===")
    for year in ["22", "23"]:
        year_stats = analyze_yearly_data(df, year)
        print(f"\nYear 20{year}:")
        print(f"- Articles: {year_stats['total_articles']:,}")
        print(f"- Size: {year_stats['total_size_gb']:.2f} GB")
        
        # export year-specific data if needed
        year_stats["data"].to_csv(f"df_{year}.csv", index=False)
    
    # print unique YYMM values for reference
    print("\n=== Time Coverage ===")
    unique_yymm = sorted(df["YYMM"].unique())
    print(f"Coverage period: {unique_yymm[0]} to {unique_yymm[-1]}")


if __name__ == "__main__":
    main()