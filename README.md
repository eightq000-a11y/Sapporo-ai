# Geometry v2 Cloud Runner

Purpose: fetch the 730 race-level sectional histories needed for 2022 VALIDATION without using the local ChatGPT container's blocked outbound HTTP.

Files:
- `manifest_2022_validation.csv`: exact required race list
- `fetch_sectionals.py`: scraper
- `.github/workflows/fetch_sectionals.yml`: GitHub Actions runner

Safety:
- FINAL_HOLDOUT race_id `202301020411` is hard-blocked in the scraper.
- Geometry-v2 parameters are not modified.
- This package only acquires race-level sectionals.

Expected output:
- `netkeiba_200m_laps_2022_validation.csv`
- `failed_urls.csv`

The workflow can be run manually with `workflow_dispatch`. It also includes a daily retry schedule so failed pages can be retried without changing the model.
