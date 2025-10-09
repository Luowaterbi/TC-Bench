import json

import random

def get_random_indices(array_length, num_indices):
    # 确保抽取的数量不超过数组长度
    if num_indices > array_length:
        return random.sample(range(array_length), array_length)

    # 使用 random.sample 抽取指定数量的索引
    indexs = random.sample(range(array_length), num_indices)
    random.shuffle(indexs)
    return indexs

def find_first_non_ac(array):
    for element in array:
        if element != "AC":
            return element
    return "AC" 

test_als = ["lcb","ht","algo","crux","predo"]
test_als = ['crux']
model_name_list = [
    "claude-sonnet-4-20250514-thinking",
    # "deepseek-v3",
    # "qwen3-235b-a22b",
    # "claude-sonnet-4-20250514",
    # "qwen3-nothink",
    # "claude4",
    # "gpt-4o",
    # "qwen-coder-plus",
    # "Qwen2.5-7B-Instruct",
    # "Qwen2.5-14B-Instruct",
    # "Qwen2.5-32B-Instruct",
    # "Qwen2.5-Coder-7B-Instruct",
    # "Qwen2.5-Coder-14B-Instruct",
    # "Qwen2.5-Coder-32B-Instruct",  
]

import os
for model_name in model_name_list:
    for test_al in test_als:
        result_file = f"ALLmode_results/tcb-{model_name}-{test_al}-{test_al}-all.json"
        if not os.path.exists(result_file):
            print(f"{model_name}-{test_al} NOT EXSIT!")
            continue 
        results = json.load(open(result_file, "r", encoding="utf-8"))

        rank_result = {
            "rank1": {"AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0},
            "rank2": {"AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0},
            "rank3": {"AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0},
            "rank4": {"AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0},
            "rank5": {"AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0},
        }
        success_k = {
            "rank1": {"total": 0, "hacked": 0},
            "rank2": {"total": 0, "hacked": 0},
            "rank3": {"total": 0, "hacked": 0},
            "rank4": {"total": 0, "hacked": 0},
            "rank5": {"total": 0, "hacked": 0},
        }
        for k, v in results.items():
            rank = len(v['codes'])

            array_length = max([len(code['status']) for code in v['codes']])
            tests_index = get_random_indices(array_length, rank * 5)

            for i in range(5):
                nums_of_tests = rank * (i+1)
                tests_index_rank_i = tests_index[:nums_of_tests]
                ## 每道题计算 rate
                hacked = 0
                status_present = {
                    "AC":0, "CE": 0, "WA":0, "RE": 0, "TLE":0, "MLE":0,"EXE":0
                }

                success_k[f"rank{i+1}"]["total"] += rank
                if array_length == 0:
                    status_present['AC'] += rank
                else:
                    for code in v['codes']:
                        tests_status = [code['status'][i] for i in tests_index_rank_i] if max(tests_index_rank_i) < len(code['status']) else code['status']

                        status_present[find_first_non_ac(tests_status)] += 1
                        if find_first_non_ac(tests_status) != "AC":
                            hacked += 1
                    success_k[f"rank{i+1}"]["hacked"] += hacked / rank

                for key, value in status_present.items():
                    rank_result[f"rank{i+1}"][key] += (value / rank)

        # 创建 Markdown 表格
        algorithm_model = f"{test_al}|{model_name}"

        # 创建 Markdown 表格
        markdown_table = "| Algorithm | Model | Rank | AC | CE | WA | RE | TLE | MLE | EXE | Hack Rate |\n"
        markdown_table += "|----------|--------|------|----|----|----|----|-----|-----|-----|-----------|\n"

        for rank in rank_result:
            total = success_k[rank]["total"]
            hacked = success_k[rank]["hacked"]
            hack_rate = (hacked / len(results) * 100) if total > 0 else 0
            hack_rate = round(hack_rate, 2)  # 保留两位小数

            # 计算每个状态的百分比和数量
            status_percentages = []
            for key in rank_result[rank]:
                count = rank_result[rank][key]
                percentage = (count / len(results) * 100)
                status_percentages.append(f"{percentage:.2f}%")

            # 将每个状态的百分比和数量组合在一起
            markdown_table += f"| {algorithm_model} | {rank} | " + " | ".join(status_percentages) + f" | {hack_rate}% |\n"

        # 保存到 .md 文件
        os.makedirs(f"./rank_md", exist_ok=True)
        with open(f"./rank_md/rank_result-{model_name}-{test_al}-main_result.md", "w") as file:
            file.write(markdown_table)

        print("Markdown 文件已生成: rank_result.md")