import json
from utils import *

def only_cpp_and_dedup():
    ds = json.load(open("/data/TCB/pro2sub_only_1_substask.json", "r"))
    new_ds = {}
    for pro, subs in ds.items():
        subs = sorted(subs, key=lambda x: (x["time"], x["memory"]))
        new_subs = []
        errors = set()
        for sub in subs:
            if sub["lang"] not in ["cpp", "c"]:
                print(f"{pro} has non-cpp/c submission: {sub['lang']}")
                continue
            output_str = sub["output_str"]
            if output_str in errors:
                continue
            errors.add(output_str)
            new_subs.append(sub)
        new_subs = sorted(new_subs, key=lambda x: x["output_str"].count("A"), reverse=True)
        new_ds[pro] = new_subs
    print(f"Total {len(new_ds)} problems after filtering cpp/c and deduplication.")
    json.dump(new_ds, open("/data/TCB/final/pro2sub_only_1_substask_dedup.json", "w"), indent=4)

# only_cpp_and_dedup()


def only_aw():
    ds = json.load(open("/data/TCB/final/pro2sub_only_1_substask_dedup.json", "r"))
    new_ds = {}
    for pro, subs in ds.items():
        new_subs = []
        final_len = 0
        for sub in subs:
            output_str = sub["output_str"]
            if all(c in "AW" for c in output_str):
                new_subs.append(sub)
                final_len = max(final_len, len(output_str))
        final_subs = [sub for sub in new_subs if len(sub["output_str"]) == final_len]
        if final_subs:
            new_ds[pro] = final_subs
    print(f"Total {len(new_ds)} problems after filtering A/W submissions.") #1698
    json.dump(new_ds, open("data/pro2sub_only_1_substask_dedup_only_aw.json", "w"), indent=4)

# only_aw()


def filter_too_wrong_wrong_code():
    ds = json.load(open("data/pro2sub_only_1_substask_dedup_only_aw.json", "r"))
    new_ds = {}
    count = []
    oris = 0
    erease = 0
    for pro, subs in ds.items():
        new_subs = []
        oris += len(subs)
        for sub in subs:
            output_str = sub["output_str"]
            ratio = output_str.count("W") / len(output_str)
            if ratio <= 0.8:
                new_subs.append(sub)
            else:
                erease += 1
        if new_subs:
            new_ds[pro] = new_subs
            count.append(len(new_subs))
    print(f"Total {len(new_ds)} problems after filtering high error rate submissions.")
    print("Oris", oris, "Ereasa", erease)
    print(erease/oris)
# filter_too_wrong_wrong_code()


def add_info():
    problem_names_mapping = json.load(open("data/problem_names.json", "r"))

    wrong = json.load(open("/data/TCB/pro2sub_only_1_substask.json"))
    w_sub_cnt = {k:len(v) for k,v in wrong.items()}
    correct = json.load(open("/data/OJ/coc/correct.json"))
    c_sub_cnt = {k:len(v) for k,v in correct.items()}

    ds = json.load(open("data/pro2sub_only_1_substask_dedup_only_aw_filtered.json", "r"))
    contents_old = json.load(open("../LOJ/contents_test.json", "r"))
    contents_new = json.load(open("../LOJ/contents_new.json", "r"))
    # all_info = json.load(open("../LOJ/all_info.json", "r"))
    new_ds = {}
    for pro, subs in ds.items():
        infos = {"codes": subs}
        if pro not in c_sub_cnt:
            print(f"Problem {pro} not found in correct submissions.")
            continue
        if pro in contents_old:
            source = contents_old[pro]
        elif pro in contents_new:
            source = contents_new[pro]
        else:
            new_name = pro.split(".", 1)[-1].replace(" ", "").replace("/", "").strip()
            if new_name not in problem_names_mapping:
                print(f"Problem {pro} not found in contents.")
                continue
            correct_name = problem_names_mapping[new_name]
            path = f"/data/OJ/problems/{correct_name}/{correct_name}.json"
            try:
                meta_info = json.load(open(path))
                source = {
                    "content": meta_info["localizedContentsOfLocale"],
                    "timeLimit": meta_info["judgeInfo"]["timeLimit"],
                    "memoryLimit": meta_info["judgeInfo"]["memoryLimit"],
                    "sample": meta_info["samples"],
                }
            except FileNotFoundError:
                print(f"File not found for {correct_name}")
                continue
        assert source["timeLimit"] > 0
        infos["content"] = source["content"]
        infos["sample"] = source["sample"]
        infos["timeLimit"] = source["timeLimit"]
        infos["memoryLimit"] = source["memoryLimit"]
        infos["correct"] = c_sub_cnt[pro]
        infos["wrong"] = w_sub_cnt[pro]
        new_ds[pro] = infos
    json.dump(new_ds, open("data/pro2sub_with_info.json", "w"), indent=4)
    print(f"Total {len(new_ds)} problems with additional information.")

def rule_filter():
    ds = json.load(open("data/pro2sub_with_info.json", "r"))
    new_ds = {}
    ranks = []
    wcs = []
    for pro, infos in ds.items():
        # if infos["wrong"] + infos["correct"] < 50:
        #     print(f"Problem {pro} has too few submissions: {infos['wrong'] + infos['correct']}")
        #     continue
        # if infos["timeLimit"] > 3000 or infos["memoryLimit"] > 1024:
        #     print(f"Problem {pro} has invalid time or memory limit: {infos['timeLimit']} {infos['memoryLimit']}")
        #     continue
        wc = [c["output_str"] for c in infos["codes"] if "W" in c["output_str"]]
        matrix = transform2matrix(wc)
        rank = get_rank(matrix)
        if rank < 5:
            print(f"Problem {pro} has invalid rank: {rank}")
            continue
        if np.any(np.all(matrix == 1, axis=0)):
            print(f"Problem {pro} has all-1 column in wc matrix.")
            continue
        wcs.append(len(wc))
        infos["wc"] = wc
        infos["rank"] = rank
        new_ds[pro] = infos
        ranks.append(rank)
    json.dump(new_ds, open("data/filter_info.json", "w"), indent=4)
    print(f"Total {len(new_ds)} problems after rule filter")

    
# rule_filter()

def look_invalid():
    ds = json.load(open("data/filter_info.json", "r"))
    for pro, infos in ds.items():
        wc = infos["wc"]
        matrix = transform2matrix(wc)
        
        zero_rows = np.all(matrix == 0, axis=1)
        if np.any(zero_rows):
            zero_indices = np.where(zero_rows)[0]
            print(f"Problem {pro}: Found {len(zero_indices)} zero rows at indices {zero_indices}")
            print(f"  Corresponding output_str: {[wc[i] for i in zero_indices]}")

# look_invalid()
        
def select_correct_code():
    ds = json.load(open("/data/OJ/coc/correct.json"))
    print(f"Total {len(ds)} problems with correct codes.")
    select_correct_codes = {}
    for pro, subs in ds.items():
        subs = sorted(subs, key=lambda x: (x["time"], x["memory"]))
        selected_code = {}
        for sub in subs:
            if sub["lang"] not in ["cpp", "c"]:
                print(f"{pro} has non-cpp/c submission: {sub['lang']}")
                continue
            if sub["code"] not in selected_code:
                selected_code[sub["code"]] = sub.copy()
            if len(selected_code) >= 5:
                break
        if selected_code:
            select_correct_codes[pro] = list(selected_code.values())
    print(f"Total {len(select_correct_codes)} problems with selected correct codes.")
    json.dump(select_correct_codes, open("./data/select_correct_code.json", "w"), indent=4)

# select_correct_code()



