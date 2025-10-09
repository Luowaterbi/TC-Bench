import subprocess
import tempfile
import os
import resource
import uuid
import json

import random
from decimal import Decimal
import decimal

def custom_sample(arr, rank):
    """
    从数组中根据指定比例抽取元素，并确保如果从后30%抽取的元素超过6个，则从前70%部分补充。

    参数：
    arr: 列表，待抽取的数组。
    rank: 要抽取的元素总数量。
    
    返回：
    抽取后的结果列表。
    """
    n = len(arr)
    rank *= 2
    if rank >= n:
        return arr
    # 计算前70%和后30%的分界
    split_index = int(0.7 * n)
    if int(0.7 * rank) > split_index:
        split_index = int(0.7 * rank)
    # 从前70%部分中抽取70% rank个元素
    front_part = arr[:split_index]
    front_sample = random.sample(front_part, int(0.7 * rank))

    # 从后30%部分中抽取30% rank个元素
    back_part = arr[-6:]  # 后30%部分
    back_sample_count = int(0.3 * rank)

    # 如果从后30%部分抽取的数量超过6个，调整
    if back_sample_count > 6:
        # 需要从前70%部分补充不足的元素
        front_sample += random.sample(front_part, back_sample_count - 6)
        back_sample_count = 6  # 确保从后30%部分最多抽取6个

    back_sample = random.sample(back_part, back_sample_count)

    # 合并两部分抽取的结果
    return front_sample + back_sample

def custom_sample_ht(arr, rank):
        # 按照source进行分类
    categories = {'prompt': [], 'random': [], 'edge': []}
    
    for item in arr:
        source = item.get('source')
        if source in categories:
            categories[source].append(item)
    
    # 计算每个分类应该抽取的数量
    total_ratio = 1 + 2 + 1  # 总比例 1:2:1
    prompt_count = min(len(categories['prompt']), rank // total_ratio)
    random_count = min(len(categories['random']), 2 * rank // total_ratio)
    edge_count = min(len(categories['edge']), rank // total_ratio)
    
    # 抽取样本
    prompt_samples = random.sample(categories['prompt'], prompt_count) if len(categories['prompt']) >= prompt_count else categories['prompt']
    random_samples = random.sample(categories['random'], random_count) if len(categories['random']) >= random_count else categories['random']
    edge_samples = random.sample(categories['edge'], edge_count) if len(categories['edge']) >= edge_count else categories['edge']
    
    # 返回合并后的抽取样本
    return prompt_samples + random_samples + edge_samples

def get_rank_custom_sample(arr, rank):
    if len(arr) <= rank:
        return arr
    return random.sample(arr, rank)

def get_testcases(testcase_path):
    data = []
    if not os.path.exists(testcase_path):
        return []
    with open(testcase_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    return data

import re

def is_decimal(s):
    try:
        a = float(s)
    except:
        return False
        
    return bool(re.match(r"^-?\d+\.\d+$", s))

import time
def run_cpp_code_linux(infos, test_mode = False):
    code = infos["code"]
    time_limit = infos["time_limit"]
    memory_limit = infos["memory_limit"]
    test_cases = infos["test_cases"]
    infos["error"] = []
    infos["details"] = []
    infos["types"] = []

    if isinstance(test_cases, str):
        test_cases = get_testcases(test_cases)


    with tempfile.TemporaryDirectory() as tmpdirname:
        unique_id = uuid.uuid4()
        cpp_file = os.path.join(tmpdirname, f"{unique_id}.cpp")
        exe_file = os.path.join(tmpdirname, f"{unique_id}.out")

        # Write C++ code to file
        with open(cpp_file, "w") as f:
            f.write(code)

        # Compile the C++ code
        # Compile the C++ code
        optimization_level = infos['compileAndRunOptions']['O']
        if optimization_level == "fast":
            optimization_level = "2"
        compile_result = subprocess.run(
            ["g++", f"-O{optimization_level}", cpp_file, "-o", exe_file, f"-std={infos['compileAndRunOptions']['std']}"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            infos["error"].append("CE")
            infos["details"].append(compile_result.stderr)
            return infos

        memory_kb = int(memory_limit) * 1024 * 5
        time_limit_int = int(time_limit) // 1000 + 3
        cmd = f"ulimit -t {time_limit_int} && ulimit -v {memory_kb} && {exe_file}"
        
        # cmd = f"{exe_file}"
        for idx, testcase in enumerate(test_cases):
            if isinstance(testcase["input"], dict):
                testcase = testcase["input"]
            
            input_string = testcase["input"]
            output_string = testcase["output"]
            ## TODO：暂时跳过了，需要清理空缺输出的
            if output_string == "":
                continue

            error = ""
            try:
                result = subprocess.run(
                        cmd,
                        input=input_string,
                        text=True,
                        capture_output=True,
                        shell=True,
                        timeout=time_limit_int
                    )
                
                # 检查返回码
                if result.returncode != 0:
                    if result.returncode == 137:  # SIGKILL - 通常是内存超限
                        error = "MLE"
                        details = f"{error}: Testcase:{idx}"
                    elif result.returncode == 124:  # timeout命令的超时返回码
                        error = "TLE"
                        details = f"{error}: Testcase:{idx}"
                    else:
                        error = "RE"
                        details = f"{error}: Testcase:{idx}"
                # if not error and result.stderr:
                #     error = "RE"
                #     details = f"{error}: Testcase:{idx}"
            except subprocess.TimeoutExpired:
                error = "TLE"
                details = f"{error}: Testcase:{idx}"
            except Exception as e:
                error = "RE"
                details = f"{error}: Testcase:{idx}"
            
            if not error:
                if isinstance(output_string, float):
                    output_string = str(output_string)
                expected_lines = [line.strip() for line in output_string.splitlines()]
                actual_lines = [line.strip() for line in result.stdout.splitlines()]

                # 移除空行
                expected_lines = [line for line in expected_lines if line]
                actual_lines = [line for line in actual_lines if line]
                
                # ## 合并为一行
                actual_lines = (" ".join(actual_lines)).strip()
                expected_lines = (" ".join(expected_lines)).strip()

                # ## 小数保留 6 位
                if is_decimal(actual_lines) and is_decimal(expected_lines):
                    if abs(float(actual_lines) - float(expected_lines)) > 1e-6:
                        error = "WA"
                        details = f"{error}: Testcase:{idx}"  
                else:
                    if actual_lines != expected_lines:
                        error = "WA"
                        details = f"{error}: Testcase:{idx}"
            
            if error:
                infos["error"].append(error)
                infos["details"].append(details)
                if test_mode:
                    return infos
            if not error and not test_mode:
                error = "AC"
                details = f"{error}: Testcase:{idx}"
                infos["error"].append("AC")
                infos["details"].append(details)

        # If all test cases passed
        if test_mode and len(infos["error"]) == 0:
            infos["error"].append("AC")
            infos["details"].append("All test cases passed")
        
        return infos