#!/usr/bin/env python3
"""Create Korean-labelled descriptive figures and their aggregate data."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd


def configure_font() -> str:
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if Path(path).is_file():
            family = font_manager.FontProperties(fname=path).get_name()
            plt.rcParams["font.family"] = family
            plt.rcParams["axes.unicode_minus"] = False
            return family
    return "DejaVu Sans"


def save_plot(fig, figures: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(figures / f"{name}.png", dpi=180, bbox_inches="tight")
    fig.savefig(figures / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def line_plot(data, columns, labels, title, ylabel, figures, name):
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for column, label in zip(columns, labels):
        if column in data:
            ax.plot(data["report_year"], data[column], marker="o", label=label)
    ax.set_title(title)
    ax.set_xlabel("보고연도")
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(2020, 2026))
    if len(columns) > 1:
        ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.25)
    save_plot(fig, figures, name)


def run(panel_path: Path, output_dir: Path) -> pd.DataFrame:
    configure_font()
    frame = pd.read_parquet(panel_path)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    yearly = frame.groupby("report_year", as_index=False).agg(
        ai_disclosure_rate=("ai_disclosure", "mean"),
        mean_ai_sentence_count_all=("ai_sentence_count", "mean"),
        whole_report_concreteness=("whole_report_concreteness", "mean"),
        ai_concreteness=("ai_concreteness", "mean"),
        past_tense_share=("past_tense_share", "mean"),
        present_tense_share=("present_tense_share", "mean"),
        future_tense_share=("future_tense_share", "mean"),
        lm_uncertainty_share=("lm_uncertainty_share", "mean"),
        passive_voice_sentence_share=("passive_voice_sentence_share", "mean"),
        fog_index=("fog_index", "mean"),
        ai_lm_positive_share=("ai_lm_positive_share", "mean"),
        ai_lm_negative_share=("ai_lm_negative_share", "mean"),
        ai_lm_uncertainty_share=("ai_lm_uncertainty_share", "mean"),
        report_word_count=("report_word_count", "mean"),
    )
    yearly.to_csv(figures / "figure_aggregate_data.csv", index=False, lineterminator="\n")
    specs = [
        (["ai_disclosure_rate"], ["AI 공시 비율"], "연도별 AI 공시 비율", "firm-year 비율", "01_ai_disclosure_rate_by_year"),
        (["mean_ai_sentence_count_all"], ["평균 AI 직접 문장 수"], "연도별 평균 AI 직접 문장 수", "문장 수", "02_mean_ai_sentence_count_by_year"),
        (["whole_report_concreteness"], ["전체 보고서 구체성"], "연도별 전체 보고서 구체성", "평균 구체성", "03_whole_report_concreteness_by_year"),
        (["ai_concreteness"], ["AI 직접 문장 구체성"], "연도별 AI 직접 문장 구체성(공시 firm-year)", "평균 구체성", "04_ai_concreteness_by_year"),
        (["past_tense_share", "present_tense_share", "future_tense_share"], ["과거", "현재", "미래"], "연도별 전체 보고서 시제 비율", "finite verb 비율", "05_tense_shares_by_year"),
        (["lm_uncertainty_share"], ["LM uncertainty"], "연도별 전체 보고서 불확실성", "유효 token 비율", "06_uncertainty_by_year"),
        (["passive_voice_sentence_share"], ["수동태 문장"], "연도별 전체 보고서 수동태 비율", "spaCy 문장 비율", "07_passive_voice_by_year"),
        (["fog_index"], ["Fog Index"], "연도별 전체 보고서 Fog Index", "Fog Index", "08_fog_index_by_year"),
        (["ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share"], ["긍정", "부정", "불확실성"], "연도별 AI 직접 문장 금융사전 비율(공시 firm-year)", "AI 유효 token 비율", "09_ai_sentiment_by_year"),
        (["report_word_count"], ["보고서 단어 수"], "연도별 평균 보고서 길이", "단어 수", "10_report_length_by_year"),
    ]
    for columns, labels, title, ylabel, name in specs:
        line_plot(yearly, columns, labels, title, ylabel, figures, name)

    group_vars = {
        "whole_report_concreteness": "구체성",
        "lm_uncertainty_share": "불확실성",
        "passive_voice_sentence_share": "수동태",
        "fog_index": "Fog Index",
        "report_word_count": "보고서 길이",
        "lm_positive_share": "긍정",
        "lm_negative_share": "부정",
    }
    group_rows = []
    for (year, disclosure), group in frame.groupby(["report_year", "ai_disclosure"]):
        row = {"report_year": year, "ai_disclosure": disclosure, "N": len(group)}
        for variable in group_vars:
            row[variable] = group[variable].mean()
        group_rows.append(row)
    group_data = pd.DataFrame(group_rows)
    group_data.to_csv(figures / "figure_ai_group_data.csv", index=False, lineterminator="\n")
    for variable, label in group_vars.items():
        fig, ax = plt.subplots(figsize=(7.2, 4.4))
        for flag, flag_label in [(0, "AI 미공시"), (1, "AI 공시")]:
            subset = group_data[group_data.ai_disclosure == flag]
            ax.plot(subset.report_year, subset[variable], marker="o", label=flag_label)
        ax.set_title(f"AI 공시 여부별 연도별 {label}")
        ax.set_xlabel("보고연도")
        ax.set_ylabel(label)
        ax.set_xticks(range(2020, 2026))
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=.25)
        save_plot(fig, figures, f"appendix_ai_group_{variable}")

    changes = pd.read_csv(output_dir / "tables/table_07_within_firm_annual_changes.csv")
    changes.to_csv(figures / "figure_within_firm_change_data.csv", index=False, lineterminator="\n")
    change_labels = {
        "whole_report_concreteness": "구체성",
        "past_tense_share": "과거 시제",
        "future_tense_share": "미래 시제",
        "lm_uncertainty_share": "불확실성",
        "passive_voice_sentence_share": "수동태",
        "fog_index": "Fog Index",
        "ai_sentence_count": "AI 문장 수",
        "ai_net_tone": "AI net tone",
    }
    for variable, label in change_labels.items():
        subset = changes[changes.variable == variable]
        if subset.empty:
            continue
        fig, ax = plt.subplots(figsize=(7.2, 4.4))
        ax.axhline(0, color="black", linewidth=.8)
        ax.plot(subset.report_year, subset.mean_within_firm_change, marker="o")
        ax.set_title(f"동일 기업 내 전년 대비 {label} 평균 변화")
        ax.set_xlabel("보고연도")
        ax.set_ylabel("평균 변화량")
        ax.set_xticks(range(2021, 2026))
        ax.grid(axis="y", alpha=.25)
        save_plot(fig, figures, f"change_{variable}")
    return yearly


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.panel, args.output_dir)
