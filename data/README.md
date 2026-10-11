# Data

## File

`g6_irrigation_data.csv`: 1,460 daily rows, 1 Jan 2022 to 30 Dec 2025, Kolhapur, Maharashtra.
The last day of the download is dropped because it has no "tomorrow".

## Source

NASA POWER daily data (rain and soil wetness). Downloaded using
[Data Access Viewer / API]. Soil variable: [GWETROOT / other, confirm].
Built with `src/build_dataset.py`.

## Columns

| Column        | Meaning                                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------- |
| date          | Day (YYYY-MM-DD)                                                                                |
| rain_mm       | Rainfall, mm/day                                                                                |
| soil_wetness  | Modelled soil wetness, 0 to 1                                                                   |
| rain_cat      | None (<2.5 mm), Light (2.5-15.5 mm), Heavy (>15.5 mm)                                           |
| soil_cat      | Dry / Moderate / Wet, tertiles of soil_wetness (cut-offs: [copy from results/logs/run_log.txt]) |
| soil_next_dry | 1 if tomorrow's soil_cat is Dry, else 0                                                         |

## Notes

- Soil wetness is modelled, not sensor-measured.
- Read with `keep_default_na=False`, otherwise pandas turns the category "None" into a missing value.
