import json
import glob
import os
import random
import itertools
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

JSON_GLOB_PATTERNS = [
    '../../results/2026-03-22/test_qwen3-8b-dpo/warm/*.json',
    '../../results/2026-03-22/test_qwen3-8b/warm/*.json',
]

def _format_p_value(p):
    if p < 1e-4:
        return 'p < 1e-4'
    return f'p = {p:.4f}'


def _permutation_test_p_value(group_a, group_b, num_permutations=5000, seed=42):
    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    observed_diff = abs(mean_a - mean_b)

    combined = group_a + group_b
    n_a = len(group_a)
    exceed_count = 0
    rng = random.Random(seed)

    for _ in range(num_permutations):
        rng.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        perm_diff = abs((sum(perm_a) / len(perm_a)) - (sum(perm_b) / len(perm_b)))
        if perm_diff >= observed_diff:
            exceed_count += 1

    return (exceed_count + 1) / (num_permutations + 1)


def _annotate_pairwise_pvalues(ax, scores, y_padding_ratio=0.06, line_height_ratio=0.06):
    valid_scores = []
    for group in scores:
        valid_scores.append([v for v in group if v is not None])

    all_values = [v for group in valid_scores for v in group]
    if not all_values:
        return

    y_min = min(all_values)
    y_max = max(all_values)
    y_span = max(y_max - y_min, 1e-6)

    base_y = y_max + y_span * y_padding_ratio
    line_height = y_span * line_height_ratio

    pairs = list(itertools.combinations(range(len(valid_scores)), 2))
    for level, (i, j) in enumerate(pairs):
        data_i = valid_scores[i]
        data_j = valid_scores[j]
        if len(data_i) < 1 or len(data_j) < 1:
            continue

        p_value = _permutation_test_p_value(data_i, data_j)

        x1, x2 = i + 1, j + 1
        y = base_y + level * line_height

        ax.plot([x1, x1, x2, x2], [y, y + line_height * 0.35, y + line_height * 0.35, y], c='black', lw=1)
        ax.text((x1 + x2) * 0.5, y + line_height * 0.4, _format_p_value(p_value), ha='center', va='bottom', fontsize=9)

    top_y = base_y + len(pairs) * line_height + y_span * 0.08
    ax.set_ylim(y_min - y_span * 0.05, top_y)


def draw_fig(scores, title, labels, annotate_pvalues=False):
    fig, ax = plt.subplots(figsize=(10, 6))
    violin = ax.violinplot(scores, showmeans=False, showmedians=False, showextrema=False)

    for body in violin['bodies']:
        body.set_alpha(0.6)

    ax.boxplot(
        scores,
        positions=range(1, len(labels) + 1),
        widths=0.2,
        whis=(2.5, 97.5),
        showfliers=True,
        patch_artist=True,
        boxprops={'facecolor': 'white', 'alpha': 0.75, 'linewidth': 1.2},
        medianprops={'color': 'black', 'linewidth': 1.5},
        whiskerprops={'color': 'black', 'linewidth': 1.0},
        capprops={'color': 'black', 'linewidth': 1.0},
        flierprops={
            'marker': 'o',
            'markerfacecolor': 'black',
            'markeredgecolor': 'black',
            'markersize': 3,
            'alpha': 0.7,
        },
    )
    plt.xticks(rotation=45, ha='right')
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_ylabel('Score')
    ax.set_title(title)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    if annotate_pvalues:
        _annotate_pairwise_pvalues(ax, scores)

    plt.tight_layout()
    fig.savefig(f'{title}.pdf', format='pdf', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)


def load_patient_turns(json_patterns):
    json_files = []
    for pattern in json_patterns:
        json_files.extend(glob.glob(pattern))
    json_files = sorted(set(json_files))

    if not json_files:
        raise FileNotFoundError(
            'No JSON files found. Checked patterns: ' + '; '.join(json_patterns)
        )

    print(f'Loaded {len(json_files)} JSON files from {len(json_patterns)} candidate patterns.')

    patient_records = []
    pas_scores_empa_stage_cnt = [[] for _ in range(18)]
    pas_scores_switch = [[] for _ in range(18)]

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        conversation_history = data.get('conversation_history', [])
        know_stage_cnt = 0
        switch_cnt = 0
        pre_stage = 'start'
        patient_turns = []

        for item in conversation_history:
            if item.get('speaker') == 'Doctor':
                stage = item.get('message', {}).get('stage')
                if stage == '知识传递阶段':
                    know_stage_cnt += 1
                if stage != pre_stage:
                    switch_cnt += 1
                    pre_stage = stage
            elif item.get('speaker') == 'Patient':
                message = item.get('message', {})
                ccs = message.get('ccs_score')
                ess = message.get('ess_score')
                pas = message.get('pas_score')
                if ccs is None or ess is None or pas is None:
                    continue
                ews = 100 - ess
                patient_turns.append({'CCS': float(ccs), 'EWS': float(ews), 'APS': float(pas)})

        if len(patient_turns) >= 2:
            patient_id = os.path.basename(json_file)
            patient_records.append({'patient_id': patient_id, 'turns': patient_turns})

        if patient_turns:
            last_pas = patient_turns[-1]['APS']
            if 0 <= know_stage_cnt < len(pas_scores_empa_stage_cnt):
                pas_scores_empa_stage_cnt[know_stage_cnt].append(last_pas)
            if 0 <= switch_cnt < len(pas_scores_switch):
                pas_scores_switch[switch_cnt].append(last_pas)

    return patient_records, pas_scores_empa_stage_cnt, pas_scores_switch


def build_lagged_dataframe(patient_records):
    rows = []
    for record in patient_records:
        patient_id = record['patient_id']
        turns = record['turns']
        df_turns = pd.DataFrame(turns)

        for col in ['CCS', 'EWS', 'APS']:
            df_turns[col] = df_turns[col] - df_turns[col].mean()

        for t in range(len(df_turns) - 1):
            rows.append({
                'patient_id': patient_id,
                'CCS_t': df_turns.loc[t, 'CCS'],
                'EWS_t': df_turns.loc[t, 'EWS'],
                'APS_t': df_turns.loc[t, 'APS'],
                'CCS_t1': df_turns.loc[t + 1, 'CCS'],
                'EWS_t1': df_turns.loc[t + 1, 'EWS'],
                'APS_t1': df_turns.loc[t + 1, 'APS'],
            })

    lagged_df = pd.DataFrame(rows)
    if lagged_df.empty:
        raise ValueError('No lagged observations could be constructed.')
    return lagged_df


def fit_cluster_robust_lagged_regression(lagged_df, outcome_name, predictor_cols=('CCS_t', 'EWS_t', 'APS_t')):
    X = sm.add_constant(lagged_df[list(predictor_cols)], has_constant='add')
    y = lagged_df[outcome_name]

    ols = sm.OLS(y, X).fit()
    robust = ols.get_robustcov_results(cov_type='cluster', groups=lagged_df['patient_id'])

    params = pd.Series(robust.params, index=X.columns)
    pvalues = pd.Series(robust.pvalues, index=X.columns)

    x_std = lagged_df[list(predictor_cols)].std(ddof=0)
    y_std = y.std(ddof=0)
    beta_std = params[list(predictor_cols)] * (x_std / y_std)

    return {
        'outcome': outcome_name,
        'params_raw': params,
        'pvalues': pvalues,
        'beta_std': beta_std,
        'rsquared': robust.rsquared,
        'n_obs': int(len(y)),
        'n_patients': int(lagged_df['patient_id'].nunique()),
        'predictor_cols': list(predictor_cols),
    }


def run_cross_lagged_analysis(patient_records):
    lagged_df = build_lagged_dataframe(patient_records)
    results = []

    print(f'\nTotal patients for lagged analysis: {len(patient_records)}')
    print(f'Total lagged observations: {len(lagged_df)}')

    for outcome in ('CCS_t1', 'EWS_t1', 'APS_t1'):
        result = fit_cluster_robust_lagged_regression(lagged_df, outcome)
        results.append(result)

        print(f"\n--- Outcome: {outcome} ---")
        # print(f"  n_obs = {result['n_obs']}")
        # print(f"  n_patients = {result['n_patients']}")
        # print('  coefficients shown below are standardized betas; p-values use patient-clustered robust SEs')
        # print(f"  {'const':>6s}: raw={result['params_raw']['const']:+.4f}  p={result['pvalues']['const']:.4g}")
        for pred in result['predictor_cols']:
            pval = result['pvalues'][pred]
            sig = '***P < 0.001' if pval < 0.001 else ('**P < 0.01' if pval < 0.01 else ('*P < 0.05' if pval < 0.05 else 'p >= 0.05'))
            print(
                f"  {pred.replace('_t', ''):>6s}: "
                f"β_std={result['beta_std'][pred]:+.4f}  "
                f"raw={result['params_raw'][pred]:+.4f} {sig}"
            )
        print(f"  R² = {result['rsquared']:.4f}")

    return results, lagged_df

if __name__ == '__main__':
    patient_records, pas_scores_empa_stage_cnt, pas_scores_switch = load_patient_turns(JSON_GLOB_PATTERNS)

    results, lagged_df = run_cross_lagged_analysis(
        patient_records,
    )
