"""Settings for practicum evaluation intelligence.

Paths and rules are listed to prevent hard-coded values from being spread across the code. If you need to change the data file, output folders, or review thresholds, start by checking here.

The values are specific to the current umssw capstone project and can be updated, adapting the pipeline.
"""

from __future__ import annotations

from pathlib import Path

project_root = Path(__file__).resolve().parent
data_dir = project_root / "data"
outputs_dir = project_root / "outputs"
tables_dir = outputs_dir / "tables"
figures_dir = outputs_dir / "figures"
profiles_dir = outputs_dir / "agency_profiles"

input_file = data_dir / "feedback_hernandez_20260326_v1.csv"

# program-level competency scores by academic year
# rows: one per program_level + academic_year combination
# columns: program_level, academic_year, competency_1 through competency_9
competency_file = data_dir / "competency_scores_by_year.csv"

agency_profiles_file = profiles_dir / "agency_profiles.csv"
agency_trends_file = tables_dir / "agency_yearly_trends.csv"
evaluations_text_file = tables_dir / "evaluations_text.csv"

# agency inclusion rule
min_responses = 3

# concern flag thresholds
concern_fit_score = 3.5
concern_sentiment = 0.05
concern_admin_overload = 40.0
concern_supervision_least = 25.0
concern_recommendation = 0.70
concern_threshold = 2

# misalignment thresholds
misalignment_comp_floor = 85.0
misalignment_sentiment_ceiling = 0.10
misalignment_admin_ceiling = 35.0

# trend threshold
declining_threshold = 0.30

# output settings
figure_dpi = 300

# dashboard
app_title = "practicum evaluation intelligence"
