import argparse
import json
from pathlib import Path

MAX_TURNS = 15

def get_average_scores(scores: list[list[float]]):
    max_len = max([len(score) for score in scores])
    assert max_len == MAX_TURNS, f"Max turns is set to {MAX_TURNS}, but found a score with length {max_len}. Please check the input data."
    sum_scores = [0 for _ in range(MAX_TURNS)]
    for score in scores:
        for i in range(MAX_TURNS):
            sum_scores[i] += score[i]
    avg_scores = [sum_score / len(scores) for sum_score in sum_scores]
    return avg_scores

def get_patient_scores(input_dir: Path):
    print(input_dir)
    """返回 avg_ccs_scores, avg_ess_scores, avg_pas_scores，以及 last_ccs_score, max_ess_score, last_ess_score, last_pas_score"""
    ccs_scores = []
    ess_scores = []
    pas_scores = []
    for input_file in input_dir.glob('**/*.json'):
        with open(input_file, encoding='utf-8') as f:
            data = json.load(f)
            if data["negotiation_result"] in ["error"]:
                continue
            patient_scores = data['scores']['patient_scores']
            ccs_scores_by_turn = []
            ess_scores_by_turn = []
            pas_scores_by_turn = []
            for i in range(MAX_TURNS):
                if i < len(patient_scores):
                    score = patient_scores[i]
                else:
                    if data["negotiation_result"] == "accept":
                        score = {
                            "ccs_score": 100.0,
                            "ess_score": 0.0,
                            "pas_score": 100.0,
                        }
                    elif data["negotiation_result"] == "reject":
                        score = {
                            "ccs_score": 0.0,
                            "ess_score": 100.0,
                            "pas_score": 0.0,
                        }
                ccs_scores_by_turn.append(score['ccs_score'])
                ess_scores_by_turn.append(score['ess_score'])
                pas_scores_by_turn.append(score['pas_score'])
            ccs_scores.append(ccs_scores_by_turn)
            ess_scores.append(ess_scores_by_turn)
            pas_scores.append(pas_scores_by_turn)
    avg_ccs_scores = get_average_scores(ccs_scores)
    avg_ess_scores = get_average_scores(ess_scores)
    avg_pas_scores = get_average_scores(pas_scores)
    last_ccs_score = avg_ccs_scores[-1]
    max_ess_score = max(avg_ess_scores)
    last_ess_score = avg_ess_scores[-1]
    last_pas_score = avg_pas_scores[-1]
    return last_ccs_score, max_ess_score, last_ess_score, last_pas_score

def update_dict(dict_1: dict, dict_2: dict):
    for key_1, value_1 in dict_1.items():
        # 如果 value_1 是 dict:
        if isinstance(value_1, dict):
            for key_2, value_2 in value_1.items():
                # 如果 value_2 是 float 或者 int，则 dict_1 中累加
                if isinstance(value_2, (float, int)):
                    dict_1[key_1][key_2] += dict_2[key_1][key_2]
        else:
            # 如果 value_1 是 float 或者 int，则 dict_1 中累加
            if isinstance(value_1, (float, int)):
                dict_1[key_1] += dict_2[key_1]
    return dict_1

def average_dict(dict_1: dict, num: int):
    for key_1, value_1 in dict_1.items():
        # 如果 value_1 是 dict:
        if isinstance(value_1, dict):
            for key_2, value_2 in value_1.items():
                # 如果 value_2 是 float 或者 int，则 dict_1 中平均
                if isinstance(value_2, (float, int)):
                    dict_1[key_1][key_2] /= num
        else:
            # 如果 value_1 是 float 或者 int，则 dict_1 中平均
            if isinstance(value_1, (float, int)):
                dict_1[key_1] /= num
    return dict_1

def get_judge_scores(input_dir: Path):
    sum_judge_doctor_scores = {
        "safety_evaluation": {
            "medical_factual_errors_score": 0.0,
            "inappropriate_assurance_overconfidence_score": 0.0,
            "risk_concealment_score": 0.0,
            "evidence_support_consistency_score": 0.0,
        },
        "humanity_evaluation": {
            "information_comprehensibility_score": 0.0,
            "response_quality_score": 0.0,
            "respect_nonjudgment_score": 0.0,
            "autonomy_support_score": 0.0,
        },
        "coverage_evaluation": {
            "coverage_percentage": 0.0,
        },
        "stage_correct_percentage": 0.0,
    }
    num_files = 0
    for input_file in input_dir.glob('**/*.json'):
        with open(input_file, encoding='utf-8') as f:
            data = json.load(f)
            if data["negotiation_result"] in ["error"]:
                continue
            judge_doctor_scores = data['scores']['judge_doctor_scores']
            sum_judge_doctor_scores = update_dict(sum_judge_doctor_scores, judge_doctor_scores)
            num_files += 1
    avg_judge_doctor_scores = average_dict(sum_judge_doctor_scores, num_files)
    return avg_judge_doctor_scores

def get_statistics(dataset_name: str, model_name: str, framework_type: str, input_dir: Path):
    last_ccs_score, max_ess_score, last_ess_score, last_pas_score = get_patient_scores(input_dir / f"{dataset_name}_{model_name}" / framework_type)
    avg_judge_doctor_scores = get_judge_scores(input_dir / f"{dataset_name}_{model_name}" / framework_type)

    return {
        "patient_scores": {
            "last_ccs_score": last_ccs_score,
            "max_ess_score": max_ess_score,
            "last_ess_score": last_ess_score,
            "last_pas_score": last_pas_score,
        },
        "judge_doctor_scores": avg_judge_doctor_scores,
    }

def render_results(results: dict):
    out = '|Framework Type|Model Name|Medical Factual Errors Score|Inappropriate Assurance Overconfidence Score|Risk Concealment Score|Evidence Support Consistency Score|Respect Nonjudgment Score|Autonomy Support Score|Response Quality Score|Information Comprehensibility Score|Coverage Percentage|Stage Correct Percentage|\n'
    out += '|---|---|---|---|---|---|---|---|---|---|---|---|\n'
    for framework_type, models in results.items():
        for model_name, stats in models.items():
            judge_doctor_scores = stats["judge_doctor_scores"]
            out += f'|{framework_type}|{model_name}|{judge_doctor_scores["safety_evaluation"]["medical_factual_errors_score"]:.2f}|{judge_doctor_scores["safety_evaluation"]["inappropriate_assurance_overconfidence_score"]:.2f}|{judge_doctor_scores["safety_evaluation"]["risk_concealment_score"]:.2f}|{judge_doctor_scores["safety_evaluation"]["evidence_support_consistency_score"]:.2f}|{judge_doctor_scores["humanity_evaluation"]["respect_nonjudgment_score"]:.2f}|{judge_doctor_scores["humanity_evaluation"]["autonomy_support_score"]:.2f}|{judge_doctor_scores["humanity_evaluation"]["response_quality_score"]:.2f}|{judge_doctor_scores["humanity_evaluation"]["information_comprehensibility_score"]:.2f}|{judge_doctor_scores["coverage_evaluation"]["coverage_percentage"]:.2f}|{judge_doctor_scores["stage_correct_percentage"]:.2f}|\n'

    out += '\n\n'

    out += '|Framework Type|Model Name|Last CCS Score|Last ESS Score|Max ESS Score|Last PAS Score|\n'
    out += '|---|---|---|---|---|---|\n'
    for framework_type, models in results.items():
        for model_name, stats in models.items():
            out += f'|{framework_type}|{model_name}|{stats["patient_scores"]["last_ccs_score"]:.2f}|{stats["patient_scores"]["last_ess_score"]:.2f}|{stats["patient_scores"]["max_ess_score"]:.2f}|{stats["patient_scores"]["last_pas_score"]:.2f}|\n'
    return out

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plot the results of the experiments.')
    parser.add_argument('--input_dir', type=str, required=True, help='Path to the input directory containing the results.')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    results = {}
    for subdir in input_dir.iterdir():
        if subdir.is_dir():
            dataset_name = subdir.name.split('_')[0]
            model_name = subdir.name.split('_')[-1]
            for subsubdir in subdir.iterdir():
                if subsubdir.is_dir():
                    framework_type = subsubdir.name
                    if framework_type not in results:
                        results[framework_type] = {}
                    results[framework_type][model_name] = get_statistics(dataset_name, model_name, framework_type, input_dir)

    out = render_results(results)
    with open(input_dir / 'results_summary.txt', 'w') as f:
        f.write(out)
    