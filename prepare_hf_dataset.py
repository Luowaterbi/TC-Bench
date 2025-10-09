"""
Convert TestcaseBench-v29.json to HuggingFace Dataset format
Remove Chinese content and intermediate processing fields
"""
import json
from datasets import Dataset, DatasetDict
from typing import Dict, Any

def clean_solution(solution: Dict[str, Any]) -> Dict[str, str]:
    """Keep only essential fields from solution"""
    return {
        "code": solution["code"],
        "lang": solution["lang"]
    }

def clean_wrong_code(wrong: Dict[str, Any]) -> Dict[str, str]:
    """Keep code, lang, and output_str (error pattern) from wrong code"""
    return {
        "code": wrong["code"],
        "lang": wrong["lang"],
        "output_str": wrong.get("output_str", "")  # Error pattern (A/W string)
    }

def clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean entry: remove Chinese fields, keep only English content
    """
    wrong_code_list = entry.get("wrong_code", [])
    wrong_code_len = len(wrong_code_list)
    original_rank = entry.get("rank", wrong_code_len)

    # Use len(wrong_code) if rank is inconsistent
    rank = wrong_code_len if original_rank != wrong_code_len else original_rank

    cleaned = {
        # English identifiers only
        "problem_id": entry.get("tcb_id_en", entry["tcb_id"]),

        # English problem description only
        "description": entry.get("query_en", ""),

        # Constraints
        "time_limit": entry["runtime_limit"],
        "memory_limit": entry["memory_limit"],

        # Sample test cases
        "sample_input": entry.get("sample", {}).get("input", "") if isinstance(entry.get("sample"), dict) else "",
        "sample_output": entry.get("sample", {}).get("output", "") if isinstance(entry.get("sample"), dict) else "",

        # Accepted solutions (cleaned)
        "solutions": [clean_solution(sol) for sol in entry["solutions"]],

        # Wrong solutions with error patterns (cleaned)
        "wrong_solutions": [clean_wrong_code(w) for w in wrong_code_list],

        # Rank: use len(wrong_code) when inconsistent
        "rank": rank,
    }

    return cleaned

def convert_to_hf_format(input_file: str = "TestcaseBench-v29.json",
                         output_dir: str = "./testcase_bench_hf"):
    """
    Convert benchmark to HuggingFace dataset format

    Args:
        input_file: Path to input JSON file
        output_dir: Directory to save HuggingFace dataset
    """
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total entries: {len(data)}")

    # Clean all entries
    print("Cleaning entries (removing Chinese content and intermediate fields)...")
    cleaned_data = []
    rank_adjusted = 0

    for i, entry in enumerate(data):
        try:
            original_rank = entry.get("rank", 0)
            wrong_len = len(entry.get("wrong_code", []))
            if original_rank != wrong_len:
                rank_adjusted += 1

            cleaned = clean_entry(entry)
            cleaned_data.append(cleaned)
        except Exception as e:
            print(f"Warning: Error processing entry {i}: {e}")
            continue

    print(f"Successfully cleaned {len(cleaned_data)} entries")
    print(f"Adjusted rank for {rank_adjusted} entries (used len(wrong_code))")

    # Create HuggingFace dataset
    print("\nCreating HuggingFace dataset...")
    dataset = Dataset.from_list(cleaned_data)

    dataset_dict = DatasetDict({
        'test': dataset  # All data is benchmark test data
    })

    # Print statistics
    print("\n" + "="*60)
    print("Dataset Statistics:")
    print("="*60)
    print(f"Total test samples: {len(dataset_dict['test'])}")
    print(f"\nFields in cleaned dataset:")
    for field in cleaned_data[0].keys():
        print(f"  - {field}")

    print(f"\nSample entry:")
    print(f"  problem_id: {cleaned_data[0]['problem_id']}")
    print(f"  solutions: {len(cleaned_data[0]['solutions'])} accepted codes")
    print(f"  wrong_solutions: {len(cleaned_data[0]['wrong_solutions'])} wrong codes")
    print(f"  rank: {cleaned_data[0]['rank']}")
    print(f"  time_limit: {cleaned_data[0]['time_limit']}ms")
    print(f"  memory_limit: {cleaned_data[0]['memory_limit']}MB")

    # Save to disk
    print(f"\nSaving dataset to {output_dir}...")
    dataset_dict.save_to_disk(output_dir)

    # Also save as JSON for easy inspection
    json_output = output_dir + "_cleaned.json"
    print(f"Saving cleaned JSON to {json_output}...")
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print("\n✅ Dataset conversion complete!")
    print(f"\nRemoved fields:")
    removed = ['query', 'tcb_id', 'balance_var', 'balance_column_sum', 'n_rows']
    for field in removed:
        print(f"  - {field}")

    print(f"\nCleaned nested fields:")
    print(f"  - solutions: kept only 'code' and 'lang'")
    print(f"  - wrong_solutions: kept only 'code', 'lang', and 'output_str'")

    return dataset_dict

def preview_dataset(output_dir: str = "./testcase_bench_hf"):
    """Preview the created dataset"""
    from datasets import load_from_disk

    print("\n" + "="*60)
    print("Dataset Preview")
    print("="*60)

    dataset = load_from_disk(output_dir)

    print("\nDataset structure:")
    print(dataset)

    print("\nFirst example from test set:")
    example = dataset['test'][0]
    print(f"\nProblem ID: {example['problem_id']}")
    print(f"Description length: {len(example['description'])} chars")
    print(f"Time limit: {example['time_limit']}ms")
    print(f"Memory limit: {example['memory_limit']}MB")
    print(f"Solutions: {len(example['solutions'])}")
    print(f"Wrong solutions: {len(example['wrong_solutions'])}")
    print(f"Rank: {example['rank']}")

    if example['wrong_solutions']:
        print(f"\nSample wrong solution error pattern: {example['wrong_solutions'][0]['output_str']}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert TestcaseBench to HuggingFace format")
    parser.add_argument("--input", default="TestcaseBench-v29.json",
                       help="Input JSON file path")
    parser.add_argument("--output", default="./testcase_bench_hf",
                       help="Output directory for HuggingFace dataset")
    parser.add_argument("--preview", action="store_true",
                       help="Preview the dataset after conversion")

    args = parser.parse_args()

    # Convert
    dataset_dict = convert_to_hf_format(args.input, args.output)

    # Preview if requested
    if args.preview:
        preview_dataset(args.output)
