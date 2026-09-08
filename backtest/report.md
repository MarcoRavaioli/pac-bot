# Risultati Fase 2 — Backtest

Soglie di accettazione (Fase 3), fissate prima di eseguire il backtest, valide allo stesso modo per le strategie originali e per quelle emerse dalla ricerca:

- CAGR out-of-sample (2020-oggi) >= CAGR buy&hold + 2%
- Sharpe out-of-sample non peggiore di buy&hold
- Max drawdown out-of-sample non oltre -75%
- Vantaggio medio sui 5 sotto-periodi (candidato - buy&hold) >= 0% (rivisto il 2026-09-08, sostituisce il conteggio delle vittorie — vedi piano-strategia-alto-rischio.md)

## Verdetto per asset/strategia (out-of-sample 2020-oggi)

| asset                            | strategy           |   oos_cagr |   oos_cagr_buyhold |   oos_max_dd |   oos_sharpe |   oos_sharpe_buyhold | subperiods_beaten   |   avg_subperiod_edge | edge_ok   | dd_ok   | sharpe_ok   | subperiods_ok   | PASSED   |
|:---------------------------------|:-------------------|-----------:|-------------------:|-------------:|-------------:|---------------------:|:--------------------|---------------------:|:----------|:--------|:------------|:----------------|:---------|
| LQQ                              | mean_reversion     |     -0.66% |             29.53% |      -66.70% |       13.34% |               82.26% | 0/5                 |              -37.22% | False     | True    | False       | False           | False    |
| LQQ                              | momentum           |     17.53% |             29.53% |      -27.68% |       78.35% |               82.26% | 1/5                 |              -20.47% | False     | True    | False       | False           | False    |
| LQQ                              | vol_target         |     13.58% |             29.53% |      -27.73% |       85.05% |               82.26% | 1/5                 |              -21.72% | False     | True    | True        | False           | False    |
| LQQ                              | sma_underlying_200 |     40.24% |             29.53% |      -35.23% |      119.36% |               82.26% | 2/5                 |                5.09% | True      | True    | True        | True            | True     |
| QQQ3                             | mean_reversion     |     -4.80% |             34.23% |      -84.14% |       13.11% |               77.77% | 0/5                 |              -51.56% | False     | False   | False       | False           | False    |
| QQQ3                             | momentum           |     18.39% |             34.23% |      -49.16% |       65.29% |               77.77% | 1/5                 |              -31.89% | False     | True    | False       | False           | False    |
| QQQ3                             | vol_target         |     12.26% |             34.23% |      -26.59% |       78.15% |               77.77% | 1/5                 |              -39.59% | False     | True    | True        | False           | False    |
| QQQ3                             | sma_underlying_200 |     61.59% |             34.23% |      -43.71% |      119.43% |               77.77% | 2/5                 |               12.90% | True      | True    | True        | True            | True     |
| XS2D                             | mean_reversion     |     -0.15% |             22.74% |      -59.35% |       12.87% |               75.08% | 0/5                 |              -21.73% | False     | True    | False       | False           | False    |
| XS2D                             | momentum           |     12.41% |             22.74% |      -20.95% |       73.56% |               75.08% | 1/5                 |              -13.87% | False     | True    | False       | False           | False    |
| XS2D                             | vol_target         |     10.18% |             22.74% |      -22.77% |       66.63% |               75.08% | 1/5                 |              -11.91% | False     | True    | False       | False           | False    |
| XS2D                             | sma_underlying_200 |     31.28% |             22.74% |      -19.38% |      124.28% |               75.08% | 2/5                 |                6.30% | True      | True    | True        | True            | True     |
| 3USL                             | mean_reversion     |      2.12% |             23.78% |      -69.31% |       25.70% |               66.91% | 0/5                 |              -21.26% | False     | True    | False       | False           | False    |
| 3USL                             | momentum           |     17.85% |             23.78% |      -25.16% |       77.04% |               66.91% | 2/5                 |              -15.67% | False     | True    | True        | False           | False    |
| 3USL                             | vol_target         |      8.66% |             23.78% |      -23.79% |       57.47% |               66.91% | 1/5                 |              -16.70% | False     | True    | False       | False           | False    |
| 3USL                             | sma_underlying_200 |     44.31% |             23.78% |      -27.86% |      119.14% |               66.91% | 2/5                 |               12.26% | True      | True    | True        | True            | True     |
| HFEA(QQQ3+3BUL)                  | hfea               |     17.17% |             34.23% |      -69.53% |       60.05% |               77.77% | 1/5                 |              -25.21% | False     | True    | False       | False           | False    |
| HFEA(3USL+3BUL)                  | hfea               |     10.93% |             23.78% |      -55.61% |       48.87% |               66.91% | 1/5                 |              -11.86% | False     | True    | False       | False           | False    |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      |     33.02% |             30.85% |      -70.85% |       80.88% |               76.79% | 1/5                 |               -6.89% | True      | True    | True        | False           | False    |


## Dettaglio per sotto-periodo

| asset                            | strategy           | period                |    cagr |   max_dd |   sharpe |   n_trades |   cum_return |   buyhold_cum_return | beats_buyhold   |
|:---------------------------------|:-------------------|:----------------------|--------:|---------:|---------:|-----------:|-------------:|---------------------:|:----------------|
| LQQ                              | mean_reversion     | 2013-2015             |  16.10% |  -28.97% |   77.20% |   4200.00% |       57.43% |              245.98% | False           |
| LQQ                              | mean_reversion     | 2016-2019             |   6.82% |  -30.27% |   39.79% |   5800.00% |       30.72% |              212.99% | False           |
| LQQ                              | mean_reversion     | 2020 (crash+recupero) | -17.67% |  -49.45% |  -30.96% |   1200.00% |      -17.99% |               69.45% | False           |
| LQQ                              | mean_reversion     | 2021-2022 (bear)      | -30.26% |  -61.03% |  -85.27% |   2900.00% |      -52.12% |              -28.76% | False           |
| LQQ                              | mean_reversion     | 2023-oggi             |  25.03% |  -35.75% |  100.87% |   5700.00% |      130.05% |              362.98% | False           |
| LQQ                              | momentum           | 2013-2015             |  11.56% |  -32.50% |   60.20% |   4900.00% |       39.45% |              245.98% | False           |
| LQQ                              | momentum           | 2016-2019             |   6.74% |  -30.97% |   42.88% |   5100.00% |       30.32% |              212.99% | False           |
| LQQ                              | momentum           | 2020 (crash+recupero) |  38.45% |  -22.85% |  109.13% |   1300.00% |       39.35% |               69.45% | False           |
| LQQ                              | momentum           | 2021-2022 (bear)      |   9.65% |  -19.96% |   56.14% |   2400.00% |       20.72% |              -28.76% | True            |
| LQQ                              | momentum           | 2023-oggi             |  17.36% |  -27.68% |   81.51% |   5500.00% |       81.66% |              362.98% | False           |
| LQQ                              | vol_target         | 2013-2015             |  21.96% |  -11.49% |  129.04% |  73900.00% |       82.85% |              245.98% | False           |
| LQQ                              | vol_target         | 2016-2019             |  15.01% |  -18.46% |   92.86% |  98400.00% |       76.39% |              212.99% | False           |
| LQQ                              | vol_target         | 2020 (crash+recupero) |  21.88% |  -17.36% |  125.20% |  25700.00% |       22.36% |               69.45% | False           |
| LQQ                              | vol_target         | 2021-2022 (bear)      |  -2.00% |  -27.73% |   -3.76% |  51500.00% |       -4.04% |              -28.76% | True            |
| LQQ                              | vol_target         | 2023-oggi             |  20.67% |  -18.64% |  122.79% |  94000.00% |      101.57% |              362.98% | False           |
| LQQ                              | sma_underlying_200 | 2013-2015             |  45.75% |  -21.83% |  148.09% |    700.00% |      214.25% |              245.98% | False           |
| LQQ                              | sma_underlying_200 | 2016-2019             |  31.66% |  -19.31% |  119.59% |   2700.00% |      205.41% |              212.99% | False           |
| LQQ                              | sma_underlying_200 | 2020 (crash+recupero) |  68.64% |  -35.23% |  134.94% |    500.00% |       70.40% |               69.45% | True            |
| LQQ                              | sma_underlying_200 | 2021-2022 (bear)      |  18.60% |  -21.69% |   79.49% |    600.00% |       41.72% |              -28.76% | True            |
| LQQ                              | sma_underlying_200 | 2023-oggi             |  46.94% |  -25.14% |  137.14% |    900.00% |      320.20% |              362.98% | False           |
| QQQ3                             | mean_reversion     | 2013-2015             |  38.74% |  -35.83% |  114.44% |   5200.00% |      168.10% |              315.09% | False           |
| QQQ3                             | mean_reversion     | 2016-2019             |  15.37% |  -34.88% |   58.79% |   6400.00% |       77.48% |              383.02% | False           |
| QQQ3                             | mean_reversion     | 2020 (crash+recupero) | -39.30% |  -62.75% |  -67.66% |   1400.00% |      -39.54% |              123.29% | False           |
| QQQ3                             | mean_reversion     | 2021-2022 (bear)      | -41.58% |  -75.79% |  -70.33% |   4500.00% |      -65.79% |              -60.52% | False           |
| QQQ3                             | mean_reversion     | 2023-oggi             |  40.42% |  -41.35% |  105.00% |   6300.00% |      250.03% |              745.64% | False           |
| QQQ3                             | momentum           | 2013-2015             |  -7.18% |  -53.39% |  -17.55% |   5400.00% |      -20.09% |              315.09% | False           |
| QQQ3                             | momentum           | 2016-2019             |  14.15% |  -42.00% |   62.35% |   4500.00% |       70.08% |              383.02% | False           |
| QQQ3                             | momentum           | 2020 (crash+recupero) |  84.63% |  -32.46% |  144.92% |   1300.00% |       85.53% |              123.29% | False           |
| QQQ3                             | momentum           | 2021-2022 (bear)      |  10.82% |  -27.24% |   50.97% |   1800.00% |       22.76% |              -60.52% | True            |
| QQQ3                             | momentum           | 2023-oggi             |   9.60% |  -49.16% |   44.02% |   6900.00% |       40.27% |              745.64% | False           |
| QQQ3                             | vol_target         | 2013-2015             |  15.53% |  -11.54% |   94.20% |  74600.00% |       54.45% |              315.09% | False           |
| QQQ3                             | vol_target         | 2016-2019             |  18.34% |  -18.51% |  109.55% | 101100.00% |       96.52% |              383.02% | False           |
| QQQ3                             | vol_target         | 2020 (crash+recupero) |  24.43% |  -18.40% |  134.10% |  25400.00% |       24.65% |              123.29% | False           |
| QQQ3                             | vol_target         | 2021-2022 (bear)      |  -3.79% |  -26.59% |  -15.12% |  50300.00% |       -7.42% |              -60.52% | True            |
| QQQ3                             | vol_target         | 2023-oggi             |  19.04% |  -18.96% |  115.03% |  93000.00% |       90.24% |              745.64% | False           |
| QQQ3                             | sma_underlying_200 | 2013-2015             |  32.11% |  -25.02% |   98.13% |    700.00% |      131.35% |              315.09% | False           |
| QQQ3                             | sma_underlying_200 | 2016-2019             |  43.34% |  -36.33% |  114.08% |   2700.00% |      324.00% |              383.02% | False           |
| QQQ3                             | sma_underlying_200 | 2020 (crash+recupero) | 175.61% |  -43.71% |  175.66% |    500.00% |      177.84% |              123.29% | True            |
| QQQ3                             | sma_underlying_200 | 2021-2022 (bear)      |  17.76% |  -32.29% |   61.04% |   1000.00% |       38.57% |              -60.52% | True            |
| QQQ3                             | sma_underlying_200 | 2023-oggi             |  67.16% |  -34.68% |  128.69% |    900.00% |      565.94% |              745.64% | False           |
| XS2D                             | mean_reversion     | 2013-2015             |  20.33% |  -21.52% |  107.03% |   5200.00% |       74.63% |              104.63% | False           |
| XS2D                             | mean_reversion     | 2016-2019             |   4.70% |  -22.58% |   33.93% |   5200.00% |       20.25% |              151.35% | False           |
| XS2D                             | mean_reversion     | 2020 (crash+recupero) | -33.92% |  -59.35% |  -84.98% |   1800.00% |      -34.13% |               19.30% | False           |
| XS2D                             | mean_reversion     | 2021-2022 (bear)      |  -1.98% |  -37.89% |    7.39% |   3300.00% |       -3.92% |                0.73% | False           |
| XS2D                             | mean_reversion     | 2023-oggi             |  13.07% |  -29.51% |   71.67% |   5100.00% |       57.36% |              234.57% | False           |
| XS2D                             | momentum           | 2013-2015             |  -0.71% |  -38.34% |    4.15% |   6800.00% |       -2.13% |              104.63% | False           |
| XS2D                             | momentum           | 2016-2019             |   3.63% |  -32.69% |   32.18% |   5900.00% |       15.38% |              151.35% | False           |
| XS2D                             | momentum           | 2020 (crash+recupero) |  15.56% |  -13.61% |   79.79% |    900.00% |       15.69% |               19.30% | False           |
| XS2D                             | momentum           | 2021-2022 (bear)      |   9.34% |  -16.43% |   59.76% |   1600.00% |       19.52% |                0.73% | True            |
| XS2D                             | momentum           | 2023-oggi             |  13.69% |  -16.19% |   81.39% |   5700.00% |       60.58% |              234.57% | False           |
| XS2D                             | vol_target         | 2013-2015             |  10.50% |  -12.73% |   70.09% |  64200.00% |       35.07% |              104.63% | False           |
| XS2D                             | vol_target         | 2016-2019             |  15.99% |  -21.61% |  103.31% |  68400.00% |       81.30% |              151.35% | False           |
| XS2D                             | vol_target         | 2020 (crash+recupero) |   6.56% |  -21.70% |   45.20% |  24100.00% |        6.61% |               19.30% | False           |
| XS2D                             | vol_target         | 2021-2022 (bear)      |   1.90% |  -22.77% |   19.60% |  47500.00% |        3.83% |                0.73% | True            |
| XS2D                             | vol_target         | 2023-oggi             |  16.41% |  -18.72% |  101.50% |  89500.00% |       75.19% |              234.57% | False           |
| XS2D                             | sma_underlying_200 | 2013-2015             |  23.35% |  -13.56% |  113.66% |   1800.00% |       88.14% |              104.63% | False           |
| XS2D                             | sma_underlying_200 | 2016-2019             |  21.10% |  -20.32% |  105.34% |   1900.00% |      115.57% |              151.35% | False           |
| XS2D                             | sma_underlying_200 | 2020 (crash+recupero) |  41.62% |  -19.38% |  123.45% |   1100.00% |       42.01% |               19.30% | True            |
| XS2D                             | sma_underlying_200 | 2021-2022 (bear)      |  22.03% |  -15.61% |  101.30% |   1400.00% |       48.79% |                0.73% | True            |
| XS2D                             | sma_underlying_200 | 2023-oggi             |  34.29% |  -17.25% |  140.87% |   1900.00% |      196.82% |              234.57% | False           |
| 3USL                             | mean_reversion     | 2013-2015             |  29.80% |  -29.13% |  112.04% |   4800.00% |      119.35% |              168.80% | False           |
| 3USL                             | mean_reversion     | 2016-2019             |   7.36% |  -27.86% |   39.45% |   5400.00% |       32.98% |              238.95% | False           |
| 3USL                             | mean_reversion     | 2020 (crash+recupero) | -29.63% |  -69.31% |  -26.61% |   2200.00% |      -29.83% |                5.74% | False           |
| 3USL                             | mean_reversion     | 2021-2022 (bear)      |  -9.36% |  -61.65% |   -0.59% |   4300.00% |      -17.82% |              -12.03% | False           |
| 3USL                             | mean_reversion     | 2023-oggi             |  20.90% |  -38.04% |   78.76% |   5100.00% |      101.44% |              362.73% | False           |
| 3USL                             | momentum           | 2013-2015             | -10.97% |  -47.94% |  -52.18% |   5600.00% |      -29.54% |              168.80% | False           |
| 3USL                             | momentum           | 2016-2019             |   6.66% |  -44.54% |   42.07% |   5300.00% |       29.53% |              238.95% | False           |
| 3USL                             | momentum           | 2020 (crash+recupero) |  16.27% |  -17.93% |   66.71% |    900.00% |       16.41% |                5.74% | True            |
| 3USL                             | momentum           | 2021-2022 (bear)      |  13.74% |  -23.17% |   62.52% |   1800.00% |       29.30% |              -12.03% | True            |
| 3USL                             | momentum           | 2023-oggi             |  21.30% |  -25.16% |   91.45% |   5700.00% |      103.95% |              362.73% | False           |
| 3USL                             | vol_target         | 2013-2015             |   5.47% |  -15.28% |   41.69% |  69100.00% |       17.40% |              168.80% | False           |
| 3USL                             | vol_target         | 2016-2019             |  16.45% |  -24.15% |   99.12% |  96100.00% |       84.24% |              238.95% | False           |
| 3USL                             | vol_target         | 2020 (crash+recupero) |   3.76% |  -23.79% |   29.45% |  25400.00% |        3.79% |                5.74% | False           |
| 3USL                             | vol_target         | 2021-2022 (bear)      |   1.71% |  -23.25% |   18.50% |  50300.00% |        3.45% |              -12.03% | True            |
| 3USL                             | vol_target         | 2023-oggi             |  14.46% |  -20.52% |   89.64% |  93000.00% |       64.62% |              362.73% | False           |
| 3USL                             | sma_underlying_200 | 2013-2015             |  15.65% |  -18.20% |   70.83% |   1800.00% |       54.93% |              168.80% | False           |
| 3USL                             | sma_underlying_200 | 2016-2019             |  29.73% |  -29.55% |  101.44% |   1900.00% |      184.10% |              238.95% | False           |
| 3USL                             | sma_underlying_200 | 2020 (crash+recupero) |  60.79% |  -27.86% |  121.44% |   1100.00% |       61.40% |                5.74% | True            |
| 3USL                             | sma_underlying_200 | 2021-2022 (bear)      |  33.45% |  -21.75% |  104.49% |   1400.00% |       77.90% |              -12.03% | True            |
| 3USL                             | sma_underlying_200 | 2023-oggi             |  47.04% |  -25.63% |  130.23% |   1900.00% |      314.89% |              362.73% | False           |
| HFEA(QQQ3+3BUL)                  | hfea               | 2013-2015             |  21.97% |  -20.11% |   82.78% |    300.00% |       22.45% |              315.09% | False           |
| HFEA(QQQ3+3BUL)                  | hfea               | 2016-2019             |  32.70% |  -36.83% |  114.33% |    600.00% |      206.24% |              383.02% | False           |
| HFEA(QQQ3+3BUL)                  | hfea               | 2020 (crash+recupero) |  83.12% |  -43.62% |  148.83% |    300.00% |       82.69% |              123.29% | False           |
| HFEA(QQQ3+3BUL)                  | hfea               | 2021-2022 (bear)      | -32.84% |  -69.53% |  -74.73% |    600.00% |      -54.61% |              -60.52% | True            |
| HFEA(QQQ3+3BUL)                  | hfea               | 2023-oggi             |  40.48% |  -39.76% |  115.59% |    800.00% |      245.91% |              745.64% | False           |
| HFEA(3USL+3BUL)                  | hfea               | 2013-2015             |   8.81% |  -20.45% |   47.99% |    300.00% |        8.99% |              168.80% | False           |
| HFEA(3USL+3BUL)                  | hfea               | 2016-2019             |  25.23% |  -27.81% |  118.13% |    600.00% |      143.53% |              238.95% | False           |
| HFEA(3USL+3BUL)                  | hfea               | 2020 (crash+recupero) |  23.71% |  -44.33% |   71.30% |    300.00% |       23.60% |                5.74% | True            |
| HFEA(3USL+3BUL)                  | hfea               | 2021-2022 (bear)      | -17.02% |  -55.61% |  -37.79% |    600.00% |      -30.94% |              -12.03% | False           |
| HFEA(3USL+3BUL)                  | hfea               | 2023-oggi             |  25.33% |  -33.42% |  102.39% |    800.00% |      128.02% |              362.73% | False           |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      | 2013-2015             |  22.81% |  -29.14% |   77.60% |       nan% |       85.22% |              240.41% | False           |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      | 2016-2019             |  19.34% |  -48.37% |   65.92% |       nan% |      102.97% |              226.21% | False           |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      | 2020 (crash+recupero) |  78.47% |  -70.85% |  113.08% |       nan% |       78.88% |               79.28% | False           |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      | 2021-2022 (bear)      |  10.02% |  -47.72% |   43.87% |       nan% |       21.00% |              -43.68% | True            |
| DualMomentum(LQQ+QQQ3+XS2D+3USL) | dual_momentum      | 2023-oggi             |  36.09% |  -44.43% |   90.82% |       nan% |      210.67% |              496.65% | False           |