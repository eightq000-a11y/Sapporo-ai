# Pedigree Growth v1 — planned lineage hierarchy

Initial major ancestry families:
- Sunday Silence / Halo / Hail to Reason
- Kingmambo / Mr. Prospector / Raise a Native
- Northern Dancer
  - Sadler's Wells / Galileo
  - Danzig / Danehill
  - Storm Bird / Storm Cat
  - Nureyev
- Roberto / Hail to Reason
- Nasrullah
  - Bold Ruler
  - Never Say Die
- Native Dancer
- Turn-to / Hail to Reason

Features to derive after scrape:
1. paternal-line nearest major ancestor and generation
2. maternal-side major ancestor exposures through damsire / second damsire / deeper maternal pedigree
3. generation-decayed ancestry weights (1/2^generation)
4. sire-line × maternal-line interactions
5. TRAIN-only growth deltas by age-season bucket
6. empirical-Bayes shrinkage toward broader lineage when sample is small

No effect will be added to the official model until VALIDATION confirms it.
FINAL_HOLDOUT remains excluded.
