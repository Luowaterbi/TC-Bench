#!/usr/bin/env python3
"""
Upload TC-Bench dataset to HuggingFace Hub

Usage:
    python upload_to_hf.py --username YOUR_HF_USERNAME

Requirements:
    pip install datasets huggingface_hub
"""

import argparse
from huggingface_hub import login
from datasets import load_from_disk

def main():
    parser = argparse.ArgumentParser(description="Upload TC-Bench to HuggingFace")
    parser.add_argument("--username", type=str, required=True, help="Your HuggingFace username")
    parser.add_argument("--dataset-name", type=str, default="TC-Bench", help="Dataset name on HuggingFace")
    parser.add_argument("--dataset-dir", type=str, default="./testcase_bench_hf", help="Local dataset directory")
    parser.add_argument("--private", action="store_true", help="Make dataset private")

    args = parser.parse_args()

    # Step 1: Login to HuggingFace
    print("=" * 60)
    print("Step 1: Login to HuggingFace")
    print("=" * 60)
    print("\nYou need a HuggingFace access token.")
    print("Get it from: https://huggingface.co/settings/tokens")
    print("\nMake sure to create a token with 'write' permissions!")
    print()

    login()
    print("\n✅ Successfully logged in to HuggingFace!")

    # Step 2: Load dataset
    print("\n" + "=" * 60)
    print("Step 2: Loading dataset from local directory")
    print("=" * 60)
    print(f"\nLoading from: {args.dataset_dir}")

    dataset = load_from_disk(args.dataset_dir)
    print(f"\n✅ Dataset loaded successfully!")
    print(f"\nDataset info:")
    print(dataset)

    # Step 3: Upload to HuggingFace Hub
    print("\n" + "=" * 60)
    print("Step 3: Uploading to HuggingFace Hub")
    print("=" * 60)

    repo_id = f"{args.username}/{args.dataset_name}"
    print(f"\nUploading to: https://huggingface.co/datasets/{repo_id}")
    print(f"Private: {args.private}")
    print("\nThis may take a few minutes...")

    dataset.push_to_hub(
        repo_id,
        private=args.private
    )

    print("\n" + "=" * 60)
    print("✅ Upload Complete!")
    print("=" * 60)
    print(f"\nYour dataset is now available at:")
    print(f"https://huggingface.co/datasets/{repo_id}")
    print()
    print("You can now use it with:")
    print(f"from datasets import load_dataset")
    print(f"dataset = load_dataset('{repo_id}')")
    print()

if __name__ == "__main__":
    main()
