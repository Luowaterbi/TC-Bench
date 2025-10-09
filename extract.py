import json
import os
from collections import defaultdict
from tqdm import tqdm
from utils import transform2matrix
from solve import get_rank
def extract_jsonl(raw_dir="/data/OJ/submission", 
                  save_dir="/data/OJ/tcb/", 
                  correct_save_dir="/data/OJ/coc/"):
    pro2sub = defaultdict(list)
    # 每个问题的正确的solution
    correct = defaultdict(list)
    # 每个问题总共有多少solution
    all_pro_cnt = defaultdict(int)
    # 每个问题有多少个testcases
    pro2testcases_count = defaultdict(int)
    output_str_map = {}

    files = os.listdir(raw_dir)
    for file in tqdm(files):
        if not file.endswith(".jsonl"):
            continue

        with open(os.path.join(raw_dir, file), "r") as f:
            lines = f.readlines()
        for line in tqdm(lines):
            d = json.loads(line)
            # loj的d["progress"]["testcaseResult"]是包括public test case和private test case的执行结果的
            # public test case的hash存在d["progress"]["samples"]里面，len(d["progress"]["samples"])就是public test case的数量
            # loj是区分子任务（subtasks）和测试点（testcases）的，只有一个subtasks的在网页上才会显示出所有testcases
            # 但是当有多个subtasks时，只显示subtasks，需要点开才能看到每个testcases
            # 并且每个subtasks都会执行，但是一旦遇到错误的testcases剩下的就会跳过不执行了
            # 当只有一个subtask时，就所有的test cases都会被执行
            # d["progress"]["subtasks"]是一个list，存储所有的subtasks，每个subtasks的private test case的hash存在d["progress"]["subtasks"]["testcases"]里面
            # 被跳过的test case，对应存储的位置是一个空的dict
            if "meta" not in d:
                # print(f"meta not in d: {json.dumps(d, indent=4)}")
                continue
            if not d["meta"]["score"] or d["meta"]["score"] == 0:
                continue
            if not d["progress"]:
                # print(f"progress is empty: {json.dumps(d, indent=4)}")
                continue

            if d["progress"]["progressType"] != "Finished":
                # print(f"progressType is not Finished: {d['progress']['progressType']}")
                continue

            if "subtasks" not in d["progress"]:
                # print(f"subtasks not in d: {json.dumps(d, indent=4)}")
                continue

            if len(d["content"]) == 0:
                # print(f"content is empty: {json.dumps(d, indent=4)}")
                continue

            submission = {"id": d["meta"]["id"], "lang": d["meta"]["codeLanguage"], "status": d["meta"]["status"], "score": d["meta"]["score"], 
                    "problem": f"#{d['meta']['problem']['id']}. {d['meta']['problemTitle']}", 
                    "time": d["meta"]["timeUsed"], "memory": d["meta"]["memoryUsed"], 
                    "code": d["content"]["code"], "compileAndRunOptions": d["content"]["compileAndRunOptions"]}

            all_pro_cnt[submission["problem"]] += 1
            if d["meta"]["score"] == 100:
                correct[submission["problem"]].append(submission)
                continue

            testcases_result = d["progress"]["testcaseResult"]
            testcase_count = sum(len(sub["testcases"]) for sub in d["progress"]["subtasks"])
            
            if pro2testcases_count[submission["problem"]] == 0:
                pro2testcases_count[submission["problem"]] = testcase_count
                print(f"first time: {submission['problem']}: {testcase_count} (from sub id {submission['id']})")
            else:
                if pro2testcases_count[submission["problem"]] != testcase_count:
                    print(f"testcase count not match: {pro2testcases_count[submission['problem']]} != {testcase_count} (from sub id {submission['id']})")
                    pro2testcases_count[submission["problem"]] = max(pro2testcases_count[submission["problem"]], testcase_count)
            
            if "samples" in d["progress"]:
                for sample in d["progress"]["samples"]:
                    testcase_hash = sample["testcaseHash"]
                    sample_result = testcases_result[testcase_hash]
                    assert sample_result["score"] == 100, f"sample score not 100: {sample_result['score']}"
            
            if len(d["progress"]["subtasks"]) == 1:
                output_str = ""
                for testcase in d["progress"]["subtasks"][0]["testcases"]:
                    testcase_hash = testcase["testcaseHash"]
                    testcase_result = testcases_result[testcase_hash]
                    head_char = testcase_result["status"][0]
                    if head_char in output_str_map:
                        assert output_str_map[head_char] == testcase_result["status"], f"output string not match: {output_str_map[head_char]} != {testcase_result['status']}"
                    else:
                        output_str_map[head_char] = testcase_result["status"]
                    output_str += head_char
                submission["output_str"] = output_str
                pro2sub[submission["problem"]].append(submission)
            else:
                continue
    print(f"pros only 1 substask: {len(pro2sub)}")
    os.makedirs(save_dir, exist_ok=True)
    json.dump(pro2sub, open(os.path.join(save_dir, "pro2sub_only_1_substask.json"), "w"), indent=4)
    json.dump(pro2testcases_count, open(os.path.join(save_dir, "pro2testcases_count_1_substask.json"), "w"), indent=4)
    json.dump(all_pro_cnt, open(os.path.join(save_dir, "all_pro_cnt.json"), "w"), indent=4)
    lens = [(k, len(v)) for k, v in pro2sub.items()]
    lens.sort(key=lambda x: x[1], reverse=True)
    for k, v in lens:
        print(f"{k}: {v}")
    if correct_save_dir:
        os.makedirs(correct_save_dir, exist_ok=True)
        json.dump(correct, open(os.path.join(correct_save_dir, "correct"), "w"), indent=4)

# extract_jsonl()