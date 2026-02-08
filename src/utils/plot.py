import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def get_average_scores(scores: list[list[float]], place_holder: float):
    max_len = max([len(score) for score in scores])
    sum_scores = [0 for _ in range(max_len)]
    for score in scores:
        for i in range(max_len):
            if i < len(score):
                sum_scores[i] += score[i]
            else:
                sum_scores[i] += place_holder
    avg_scores = [sum_score / len(scores) for sum_score in sum_scores]
    return avg_scores

def get_patient_scores(input_dir: Path):
    """返回 avg_ccs_scores, avg_ess_scores, avg_pas_scores，以及 last_ccs_score, max_ess_score, last_ess_score, last_pas_score"""
    ccs_scores = []
    ess_scores = []
    pas_scores = []
    for input_file in input_dir.glob('**/*.json'):
        with open(input_file, encoding='utf-8') as f:
            data = json.load(f)
            patient_scores = data['scores']['patient_scores']
            ccs_scores_by_turn = []
            ess_scores_by_turn = []
            pas_scores_by_turn = []
            for score in patient_scores:
                ccs_scores_by_turn.append(score['ccs_score'])
                ess_scores_by_turn.append(score['ess_score'])
                pas_scores_by_turn.append(score['pas_score'])
            ccs_scores.append(ccs_scores_by_turn)
            ess_scores.append(ess_scores_by_turn)
            pas_scores.append(pas_scores_by_turn)
    avg_ccs_scores = get_average_scores(ccs_scores, place_holder=100.0)
    avg_ess_scores = get_average_scores(ess_scores, place_holder=0.0)
    avg_pas_scores = get_average_scores(pas_scores, place_holder=100.0)
    last_ccs_score = avg_ccs_scores[-1]
    max_ess_score = max(avg_ess_scores)
    last_ess_score = avg_ess_scores[-1]
    last_pas_score = avg_pas_scores[-1]
    return avg_ccs_scores, avg_ess_scores, avg_pas_scores, last_ccs_score, max_ess_score, last_ess_score, last_pas_score

def update_dict(dict_1: dict, dict_2: dict):
    for key_1, value_1 in dict_1.items():
        for key_2, value_2 in value_1.items():
            # 如果 value_2 是 float 或者 int，则 dict_1 中累加
            if isinstance(value_2, (float, int)):
                print(value_2)
                dict_1[key_1][key_2] += dict_2[key_1][key_2]
    return dict_1

def average_dict(dict_1: dict, num: int):
    for key_1, value_1 in dict_1.items():
        for key_2, value_2 in value_1.items():
            # 如果 value_2 是 float 或者 int，则 dict_1 中平均
            if isinstance(value_2, (float, int)):
                dict_1[key_1][key_2] /= num
    return dict_1

def get_judge_scores(input_dir: Path):
    sum_judge_patient_scores = {
        "persona_evaluation": {
            "personality_score": 0.0,
            "communication_style_score": 0.0,
            "education_level_score": 0.0,
            "financial_status_score": 0.0,
            "cross_turn_consistency_score": 0.0,
            "diagnosis_context_fit_score": 0.0,
        },
        "humanlikeness_evaluation": {
            "emotion_realism_score": 0.0,
            "communication_behavior_realism_score": 0.0,
            "cognitive_uncertainty_score": 0.0,
            "coping_strategy_diversity_score": 0.0,
            "human_coherence_score": 0.0,
            "overall_humanlikeness_score": 0.0,
        },
    }
    sum_judge_doctor_scores = {
        "safety_evaluation": {
            "medical_factual_errors_score": 0.0,
            "inappropriate_assurance_overconfidence_score": 0.0,
            "risk_concealment_score": 0.0,
            "noncompliant_guidance_score": 0.0,
            "evidence_support_consistency_score": 0.0,
        },
        "humanity_evaluation": {
            "information_comprehensibility_score": 0.0,
            "empathy_ack_response_quality_score": 0.0,
            "respect_nonjudgment_score": 0.0,
            "autonomy_support_score": 0.0,
        },
        "coverage_evaluation": {
            "coverage_percentage": 0.0,
        },
        "reiteration_evaluation": {
            "reiteration_percentage": 0.0,
        },
    }
    for input_file in input_dir.glob('**/*.json'):
        with open(input_file, encoding='utf-8') as f:
            data = json.load(f)
            judge_patient_scores = data['scores']['judge_patient_scores']
            judge_doctor_scores = data['scores']['judge_doctor_scores']
            sum_judge_patient_scores = update_dict(sum_judge_patient_scores, judge_patient_scores)
            sum_judge_doctor_scores = update_dict(sum_judge_doctor_scores, judge_doctor_scores)
    num_files = len(list(input_dir.glob('**/*.json')))
    avg_judge_patient_scores = average_dict(sum_judge_patient_scores, num_files)
    avg_judge_doctor_scores = average_dict(sum_judge_doctor_scores, num_files)
    return avg_judge_patient_scores, avg_judge_doctor_scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot the results of the experiments.')
    parser.add_argument('--input_dir_1', type=str, required=True, help='Path to the first input directory containing the results.')
    parser.add_argument('--input_dir_2', type=str, required=True, help='Path to the second input directory containing the results.')
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the output directory where the plots will be saved.')
    args = parser.parse_args()

    input_dir_1 = Path(args.input_dir_1)
    input_dir_2 = Path(args.input_dir_2)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    avg_ccs_scores_1, avg_ess_scores_1, avg_pas_scores_1, last_ccs_score_1, max_ess_score_1, last_ess_score_1, last_pas_score_1 = get_patient_scores(input_dir_1)
    avg_ccs_scores_2, avg_ess_scores_2, avg_pas_scores_2, last_ccs_score_2, max_ess_score_2, last_ess_score_2, last_pas_score_2 = get_patient_scores(input_dir_2)

    # 画出 CCS、ESS、PAS 随着对话轮数的变化曲线图，input_dir_1 用实线，input_dir_2 用虚线。从上到下分为三个子图，分别是 CCS、ESS、PAS。每个子图的 x 轴是对话轮数，y 轴是对应的分数。每个子图的标题分别是 "CCS Score", "ESS Score", "PAS Score"。在每个子图中添加图例，区分 input_dir_1 和 input_dir_2。
    plt.figure(figsize=(12, 18))
    plt.subplot(3, 1, 1)
    plt.plot(avg_ccs_scores_1, label='Input Directory 1', marker='o', linestyle='-', color='blue')
    plt.plot(avg_ccs_scores_2, label='Input Directory 2', marker='o', linestyle='--', color='blue')
    plt.title('CCS Score')
    plt.xlabel('Turn')
    plt.ylabel('CCS Score')
    plt.grid(True)
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(avg_ess_scores_1, label='Input Directory 1', marker='s', linestyle='-', color='green')
    plt.plot(avg_ess_scores_2, label='Input Directory 2', marker='s', linestyle='--', color='green')
    plt.title('ESS Score')
    plt.xlabel('Turn')
    plt.ylabel('ESS Score')
    plt.grid(True)
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(avg_pas_scores_1, label='Input Directory 1', marker='^', linestyle='-', color='red')
    plt.plot(avg_pas_scores_2, label='Input Directory 2', marker='^', linestyle='--', color='red')
    plt.title('PAS Score')
    plt.xlabel('Turn')
    plt.ylabel('PAS Score')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_dir / 'scores_plot.png')

    # 输出两者分别的最后一轮 CCS 分数、最大 ESS 分数、最后一轮 ESS 分数、最后一轮 PAS 分数到 results.txt 文件中
    with open(output_dir / 'results.txt', 'w') as f:
        f.write(f'Input Directory 1: {input_dir_1}\n')
        f.write(f'Last CCS Score: {last_ccs_score_1}\n')
        f.write(f'Max ESS Score: {max_ess_score_1}\n')
        f.write(f'Last ESS Score: {last_ess_score_1}\n')
        f.write(f'Last PAS Score: {last_pas_score_1}\n\n')

        f.write(f'Input Directory 2: {input_dir_2}\n')
        f.write(f'Last CCS Score: {last_ccs_score_2}\n')
        f.write(f'Max ESS Score: {max_ess_score_2}\n')
        f.write(f'Last ESS Score: {last_ess_score_2}\n')
        f.write(f'Last PAS Score: {last_pas_score_2}\n')
    
    # 记下来处理 Judge Patient 和 Judge Doctor 的结果
    avg_judge_patient_scores_1, avg_judge_doctor_scores_1 = get_judge_scores(input_dir_1)
    avg_judge_patient_scores_2, avg_judge_doctor_scores_2 = get_judge_scores(input_dir_2)

    with open(output_dir / 'judge_results_1.json', 'w') as f:
        json.dump({
            "judge_patient_scores": avg_judge_patient_scores_1,
            "judge_doctor_scores": avg_judge_doctor_scores_1,
        }, f, indent=4)
    with open(output_dir / 'judge_results_2.json', 'w') as f:
        json.dump({
            "judge_patient_scores": avg_judge_patient_scores_2,
            "judge_doctor_scores": avg_judge_doctor_scores_2,
        }, f, indent=4)
