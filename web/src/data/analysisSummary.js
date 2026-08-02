// analysis/descriptive_2020_2025/figures/figure_aggregate_data.csv에서 생성한 대시보드 표시용 요약값.
export const analysisSummary = {
  panel: { observations: 2829, companies: 545, balancedCompanies: 397, unbalancedCompanies: 148 },
  correlations: [
    { left: "past_tense_share", right: "present_tense_share", value: -0.978, sample: 2829 },
    { left: "log_report_word_count", right: "report_word_count", value: 0.930, sample: 2829 },
    { left: "ai_sentence_count", right: "log1p_ai_sentence_count", value: 1.000, sample: 2829 },
  ],
  years: [
    { year: 2020, observations: 446, disclosure: 123, aiSentenceCount: 1.378924, wholeReportConcreteness: 2.904034, aiConcreteness: 2.994354, past: 0.248259, present: 0.718120, future: 0.033622, uncertainty: 0.017067, passive: 0.297599, fog: 20.636856, reportWords: 58001.643498, aiPositive: 0.020006, aiNegative: 0.010114, aiUncertainty: 0.009760 },
    { year: 2021, observations: 462, disclosure: 144, aiSentenceCount: 1.595238, wholeReportConcreteness: 2.903048, aiConcreteness: 2.984716, past: 0.238930, present: 0.727865, future: 0.033205, uncertainty: 0.017361, passive: 0.296094, fog: 20.690612, reportWords: 56964.493506, aiPositive: 0.020457, aiNegative: 0.010528, aiUncertainty: 0.009365 },
    { year: 2022, observations: 471, disclosure: 167, aiSentenceCount: 1.872611, wholeReportConcreteness: 2.902211, aiConcreteness: 2.950700, past: 0.233149, present: 0.734080, future: 0.032770, uncertainty: 0.017452, passive: 0.296163, fog: 20.755176, reportWords: 58009.496815, aiPositive: 0.019177, aiNegative: 0.012213, aiUncertainty: 0.012284 },
    { year: 2023, observations: 479, disclosure: 327, aiSentenceCount: 6.225470, wholeReportConcreteness: 2.898762, aiConcreteness: 2.792481, past: 0.223067, present: 0.744814, future: 0.032118, uncertainty: 0.017768, passive: 0.295105, fog: 20.831561, reportWords: 58149.198330, aiPositive: 0.015607, aiNegative: 0.029624, aiUncertainty: 0.025793 },
    { year: 2024, observations: 487, disclosure: 431, aiSentenceCount: 11.706366, wholeReportConcreteness: 2.896291, aiConcreteness: 2.741148, past: 0.217387, present: 0.750354, future: 0.032259, uncertainty: 0.017991, passive: 0.295560, fog: 20.878192, reportWords: 58819.907598, aiPositive: 0.013329, aiNegative: 0.035716, aiUncertainty: 0.029559 },
    { year: 2025, observations: 484, disclosure: 468, aiSentenceCount: 17.892562, wholeReportConcreteness: 2.892021, aiConcreteness: 2.735658, past: 0.214147, present: 0.753390, future: 0.032463, uncertainty: 0.018302, passive: 0.294923, fog: 20.882516, reportWords: 59030.572314, aiPositive: 0.013919, aiNegative: 0.037193, aiUncertainty: 0.029732 },
  ],
};
