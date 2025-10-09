# TestCase-Bench: A Binary-Matrix Perspective for Test Case Quality Evaluation

Official repository for **"How Many Code and Test Cases Are Enough? Evaluating Test Cases Generation from a Binary-Matrix Perspective"**

## 📋 Overview

TestCase-Bench (TC-Bench) is a benchmark dataset for evaluating test case quality using a binary-matrix perspective. This repository contains the complete data construction pipeline for processing competitive programming submissions into a research-ready benchmark.

### Key Features

- **877 Programming Problems** with comprehensive test coverage
- **Binary-Matrix Analysis Framework** for test case evaluation
- **~7,000+ Code Solutions** including both correct and incorrect implementations
- **Error Pattern Analysis** via output strings (A/W patterns)
- **Bilingual Support** (Chinese and English problem descriptions)
- **Rich Metadata** including time/memory limits and sample test cases

## 📊 Dataset Statistics

```
Total Problems:              877
Total Solutions:             ~7,000+
Avg Solutions per Problem:   8
Languages:                   C/C++
Benchmark Test Samples:      877 (all for evaluation)
```

## 🗂️ Dataset Structure

Each entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `problem_id` | string | Problem identifier (English) |
| `description` | string | Problem statement (English) |
| `time_limit` | int | Runtime limit in milliseconds |
| `memory_limit` | int | Memory limit in MB |
| `sample_input` | string | Sample input test case |
| `sample_output` | string | Sample output test case |
| `solutions` | list | Accepted solutions with `code` and `lang` |
| `wrong_solutions` | list | Wrong solutions with `code`, `lang`, and `output_str` |
| `rank` | int | Number of distinct error patterns (matrix rank) |

### Error Patterns (`output_str`)

Each wrong solution includes an `output_str` field representing test case results:
- `A` = Accepted (passed the test case)
- `W` = Wrong Answer (failed the test case)

Example: `"AWAAAAAAAA"` means the code failed test case 1 and passed test cases 2-10.

## 🔧 Data Construction Pipeline

### Scripts Overview

1. **`extract.py`** - Extract and parse submissions from raw JSONL data
   - Filters by submission status and score
   - Handles subtask structure and test case results
   - Deduplicates by error patterns

2. **`filter.py`** - Multi-stage filtering pipeline
   - Language filtering (C/C++ only)
   - Deduplication by output patterns
   - Error rate filtering (removes >80% error submissions)
   - Adds problem metadata and constraints

3. **`solve.py`** - Binary matrix analysis and optimization
   - Transforms error patterns to binary matrices
   - Calculates matrix rank (diversity metric)
   - Finds basis vectors via QR decomposition
   - Optimizes balance using Jaccard similarity
   - Greedy iterative improvement algorithm

4. **`verify.py`** - Validation of balance metrics
   - Verifies Jaccard similarity calculations
   - Checks consistency of balance values

5. **`utils.py`** - Core utility functions
   - `transform2matrix()` - Convert A/W strings to binary matrix
   - `transform2aw()` - Convert matrix back to strings
   - `get_rank()` - Calculate matrix rank
   - `get_basis()` - Extract basis vectors
   - `cal_jaccard_similarity()` - Compute similarity metrics

6. **`prepare_hf_dataset.py`** - HuggingFace dataset conversion
   - Removes Chinese content and intermediate fields
   - Cleans nested structures
   - Adjusts ranks when inconsistent
   - Creates train/test splits

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/TC-Bench.git
cd TC-Bench

# Install dependencies
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

### 2. Convert Dataset to HuggingFace Format

```bash
python prepare_hf_dataset.py --input TestcaseBench-v29.json --output ./testcase_bench_hf --preview
```

### 3. Load and Use Dataset

```python
from datasets import load_dataset, load_from_disk

# Load from local disk
dataset = load_from_disk("./testcase_bench_hf")

# Or load from HuggingFace Hub (after upload)
dataset = load_dataset("your-username/testcase-bench")

# Access benchmark test samples
for example in dataset['test']:
    print(f"Problem: {example['problem_id']}")
    print(f"Rank: {example['rank']}")
    print(f"Solutions: {len(example['solutions'])}")
    print(f"Wrong solutions: {len(example['wrong_solutions'])}")

    # Access error patterns
    for wrong in example['wrong_solutions']:
        print(f"  Error pattern: {wrong['output_str']}")
```

## 📖 Methodology

### Binary-Matrix Perspective

The benchmark uses a novel binary-matrix approach to evaluate test case quality:

1. **Error Pattern Encoding**: Each wrong code's test results form a binary vector
   - `W` (Wrong) → 1
   - `A` (Accepted) → 0

2. **Matrix Construction**: Stack vectors to form a binary matrix where:
   - Rows = wrong code samples
   - Columns = test cases
   - Value = whether the code failed that test case

3. **Rank Analysis**: Matrix rank indicates diversity of error patterns
   - Higher rank = more distinct failure modes captured
   - Rank equals number of linearly independent error patterns

4. **Balance Optimization**: Use Jaccard similarity to find balanced test suites
   - Minimize overlap between test case detection patterns
   - Greedy iterative swap algorithm

### Key Metrics

- **Rank**: Number of distinct error patterns (diversity)
- **Balance**: Distribution quality of test case coverage
- **Coverage**: Ability to distinguish different failure modes

## 📦 HuggingFace Upload Instructions

### Option 1: Using Web UI

1. Go to https://huggingface.co/new-dataset
2. Create a new dataset repository
3. Upload `testcase_bench_hf_cleaned.json` via the Files tab
4. Add a dataset card (README.md) describing the benchmark

### Option 2: Using Python API

```bash
# Install dependencies
pip install datasets huggingface_hub

# Run upload script
python3 << EOF
from huggingface_hub import login
from datasets import load_from_disk

# Login (you'll need a HuggingFace token)
login()

# Load and push to hub
dataset = load_from_disk("./testcase_bench_hf")
dataset.push_to_hub("your-username/testcase-bench")
EOF
```

### Option 3: Using CLI

```bash
# Install HuggingFace CLI
pip install huggingface_hub

# Login to HuggingFace
huggingface-cli login

# Upload dataset
huggingface-cli upload your-username/testcase-bench ./testcase_bench_hf --repo-type=dataset
```

## 🤝 Citation

If you use TestCase-Bench in your research, please cite:

```bibtex
@article{tcbench2025,
  title={How Many Code and Test Cases Are Enough? Evaluating Test Cases Generation from a Binary-Matrix Perspective},
  author={Your Name et al.},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2025}
}
```

## 📝 License

This project is licensed under the MIT License.

## 🔮 Future Work

- Evaluation scripts and baseline models
- Automated test case generation tools
- Extended language support beyond C/C++
- Interactive analysis dashboard

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Note**: This repository contains the data construction pipeline. Evaluation code and baselines will be released in future updates.
