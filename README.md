# TC-Bench: Test Case Quality Evaluation Benchmark

[![Paper](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/datasets)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official repository for **"How Many Code and Test Cases Are Enough? Evaluating Test Cases Generation from a Binary-Matrix Perspective"**

## 📋 Overview

TC-Bench is a comprehensive benchmark for evaluating test case quality using a binary-matrix perspective. This repository contains:

1. **Data Construction Pipeline** - Scripts to build the benchmark from competitive programming submissions
2. **Test Case Filtering** - Validate generated test cases with correct solutions
3. **Evaluation Scripts** - Evaluate test cases using wrong code samples
4. **Pre-built Dataset** - Ready-to-use benchmark dataset (877 problems)

### Key Features

- **877 Programming Problems** with comprehensive test coverage
- **~7,000+ Code Solutions** including correct and incorrect implementations
- **Binary-Matrix Analysis** for test case quality evaluation
- **Error Pattern Analysis** via output strings (A/W patterns)
- **Automated Evaluation** with parallel execution support

## 📊 Dataset Statistics

```
Total Problems:              877
Total Solutions:             ~7,000+
Avg Solutions per Problem:   8
Languages:                   C/C++
Benchmark Test Samples:      877 (all for evaluation)
```

## 🗂️ Repository Structure

```
TC-Bench/
├── data_construction/         # Dataset construction & filtering
│   ├── extract.py            # Extract submissions from raw data
│   ├── filter.py             # Filter and clean benchmark dataset
│   ├── solve.py              # Binary matrix analysis & optimization
│   ├── verify.py             # Verify balance metrics
│   ├── utils.py              # Utility functions
│   ├── prepare_hf_dataset.py # Convert to HuggingFace format
│   ├── filter_testcases.py   # Filter generated test cases (with correct codes)
│   ├── excute_tool_filter.py # Execution engine for filtering
│   └── load_data_filter.py   # Data loader for filtering
│
├── evaluation/               # Evaluation scripts (test with wrong codes)
│   ├── parallel_exe.py       # Main evaluation script
│   ├── excute_tool_linux.py  # Execution engine for evaluation
│   ├── load_data.py          # Data loading utilities
│   └── get_rank_result.py    # Compute rank-based metrics
│
├── TestcaseBench-v29.json   # Main benchmark dataset
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/TC-Bench.git
cd TC-Bench
pip install -r requirements.txt
```

### Using the Pre-built Dataset

```python
from datasets import load_dataset

# Load from HuggingFace Hub
dataset = load_dataset("your-username/testcase-bench")

# Access benchmark test samples
for example in dataset['test']:
    print(f"Problem: {example['problem_id']}")
    print(f"Rank: {example['rank']}")
    print(f"Solutions: {len(example['solutions'])}")
    print(f"Wrong solutions: {len(example['wrong_solutions'])}")

    # Each wrong solution has an error pattern (output_str)
    for wrong in example['wrong_solutions']:
        print(f"  Error pattern: {wrong['output_str']}")  # e.g., "AWAAAAAAAA"
```

## 📖 Dataset Structure

Each entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `problem_id` | string | Problem identifier (English) |
| `description` | string | Problem statement (English) |
| `time_limit` | int | Runtime limit (ms) |
| `memory_limit` | int | Memory limit (MB) |
| `sample_input` | string | Sample input test case |
| `sample_output` | string | Sample output test case |
| `solutions` | list | Accepted solutions: `[{code, lang}, ...]` |
| `wrong_solutions` | list | Wrong solutions: `[{code, lang, output_str}, ...]` |
| `rank` | int | Number of distinct error patterns |

### Error Patterns (`output_str`)

- `A` = Accepted (passed the test case)
- `W` = Wrong Answer (failed the test case)

Example: `"AWAAAAAAAA"` = failed test 1, passed tests 2-10

## 🔧 Benchmark Construction Pipeline

Build the TC-Bench dataset from raw submissions:

### 1. Extract (`extract.py`)
Extract and parse submissions from JSONL files
```bash
cd data_construction
python extract.py
```

### 2. Filter (`filter.py`)
Multi-stage filtering: language, deduplication, error rate
```bash
python filter.py
```

### 3. Solve (`solve.py`)
Binary matrix analysis and balance optimization
```bash
python solve.py
```

### 4. Verify (`verify.py`)
Validate balance metrics
```bash
python verify.py
```

### 5. Convert to HuggingFace (`prepare_hf_dataset.py`)
```bash
python prepare_hf_dataset.py --input ../TestcaseBench-v29.json --output ../testcase_bench_hf
```

## 🧮 Evaluate Generated Test Cases

Use TC-Bench to evaluate your generated test cases in 3 steps:

### Step 1: Filter Generated Test Cases

Validate generated test cases using correct reference solutions (removes invalid test cases):

```bash
cd data_construction

python filter_testcases.py \
    --testcase_alg your_algorithm \
    --model_name your_model \
    --base_dir "/path/to/generated/testcases" \
    --cpu 50 \
    --data_path "../TestcaseBench-v29.json"
```

**Input Format:** Generated test cases should be JSONL files at:
```
{base_dir}/{model_name}/{testcase_alg}/tests-{problem_id}.jsonl
```

Each line:
```json
{"input": "test input", "output": "expected output"}
```

**Output:** Filtered test cases saved to:
```
save_tests_{model_name}-filter/{testcase_alg}/tests-{problem_id}.jsonl
```

### Step 2: Evaluate Against Wrong Code

Test filtered cases against wrong code samples to measure detection capability:

```bash
cd ../evaluation

python parallel_exe.py \
    --testcase_alg your_algorithm \
    --model_name your_model \
    --prefix_url "../data_construction/" \
    --cpu 50 \
    --data_path "../TestcaseBench-v29.json"
```

**Output:** Results saved to `ALLmode_results/`:
- `tcb-{model}-{alg}-{alg}.json` - Raw execution results
- `tcb-{model}-{alg}-{alg}-all.json` - Aggregated results by problem

### Step 3: Compute Metrics

Generate evaluation metrics at different rank multipliers:

```bash
python get_rank_result.py
```

Edit `get_rank_result.py` to configure models/algorithms:
```python
test_als = ["your_algorithm"]
model_name_list = ["your_model"]
```

**Output:** Markdown tables in `rank_md/`:
```
rank_md/rank_result-{model}-{alg}-main_result.md
```

### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Hack Rate** | % of wrong codes detected by generated tests |
| **Rank Multipliers** | Test with k×rank cases (k=1,2,3,4,5) |
| **AC/CE/WA/RE/TLE/MLE** | Status distribution |

**Status Codes:**
- **AC**: Accepted
- **CE**: Compilation Error
- **WA**: Wrong Answer
- **RE**: Runtime Error
- **TLE**: Time Limit Exceeded
- **MLE**: Memory Limit Exceeded

## 📖 Methodology

### Binary-Matrix Perspective

1. **Error Pattern Encoding**
   - Wrong code's test results → binary vector
   - `W` (Wrong) → 1, `A` (Accepted) → 0

2. **Matrix Construction**
   - Rows = wrong code samples
   - Columns = test cases
   - Entry = whether code failed that test

3. **Rank Analysis**
   - Matrix rank = # of distinct error patterns
   - Higher rank = more diverse failure modes
   - Rank = # of linearly independent patterns

4. **Balance Optimization**
   - Use Jaccard similarity to minimize test overlap
   - Greedy iterative swap algorithm

### Example

```
Test Cases:    T1  T2  T3  T4
WrongCode1:    W   A   A   A    →  [1, 0, 0, 0]
WrongCode2:    A   W   A   A    →  [0, 1, 0, 0]
WrongCode3:    A   A   W   A    →  [0, 0, 1, 0]

Matrix Rank = 3 (3 linearly independent patterns)
```

## 📦 Upload to HuggingFace

```bash
cd data_construction
python prepare_hf_dataset.py

# Upload
python << EOF
from huggingface_hub import login
from datasets import load_from_disk
login()
dataset = load_from_disk("../testcase_bench_hf")
dataset.push_to_hub("your-username/testcase-bench")
EOF
```

## 🤝 Citation

```bibtex
@article{tcbench2025,
  title={How Many Code and Test Cases Are Enough? Evaluating Test Cases Generation from a Binary-Matrix Perspective},
  author={Your Name et al.},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2025}
}
```

## 📝 System Requirements

- **Data Construction**: Any OS with Python 3.8+
- **Filtering & Evaluation**: Linux with g++ compiler (C++11/14/17/20)

## 🔮 Roadmap

- [x] Data construction pipeline
- [x] HuggingFace dataset conversion
- [x] Test case filtering framework
- [x] Evaluation framework
- [ ] Baseline test case generation models
- [ ] Multi-language support

## 📧 Contact

For questions or issues, please open an issue on GitHub.
