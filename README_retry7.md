# 7件だけ再取得

アップロード:
- retry_failed_sectionals.py
- retry7_manifest.csv

workflow:
- .github/workflows/retry7_sectionals.yml

このジョブは失敗7レースだけ再取得し、
既存 `netkeiba_200m_laps_2022_validation.csv` に成功分を追記、
`failed_urls.csv` を残存失敗分だけに更新します。
