# Risultati Fase 2 — Backtest

Soglie di accettazione (Fase 3), fissate prima di eseguire il backtest, valide allo stesso modo per le strategie originali e per quelle emerse dalla ricerca:

- CAGR out-of-sample (2020-oggi) >= CAGR buy&hold + 2%
- Sharpe out-of-sample non peggiore di buy&hold
- Max drawdown out-of-sample non oltre -75%
- Batte buy&hold in almeno 3/5 sotto-periodi

## Verdetto per asset/strategia (out-of-sample 2020-oggi)

| asset           | strategy           |   oos_cagr |   oos_cagr_buyhold |   oos_max_dd |   oos_sharpe |   oos_sharpe_buyhold | subperiods_beaten   | edge_ok   | dd_ok   | sharpe_ok   | subperiods_ok   | PASSED   |
|:----------------|:-------------------|-----------:|-------------------:|-------------:|-------------:|---------------------:|:--------------------|:----------|:--------|:------------|:----------------|:---------|
| LQQ             | mean_reversion     |     -0.66% |             29.53% |      -66.70% |       13.34% |               82.26% | 0/5                 | False     | True    | False       | False           | False    |
| LQQ             | momentum           |     17.53% |             29.53% |      -27.68% |       78.35% |               82.26% | 1/5                 | False     | True    | False       | False           | False    |
| LQQ             | vol_target         |     13.58% |             29.53% |      -27.73% |       85.05% |               82.26% | 1/5                 | False     | True    | True        | False           | False    |
| LQQ             | sma_underlying_200 |     40.24% |             29.53% |      -35.23% |      119.36% |               82.26% | 2/5                 | True      | True    | True        | False           | False    |
| QQQ3            | mean_reversion     |     -4.80% |             34.23% |      -84.14% |       13.11% |               77.77% | 0/5                 | False     | False   | False       | False           | False    |
| QQQ3            | momentum           |     18.39% |             34.23% |      -49.16% |       65.29% |               77.77% | 1/5                 | False     | True    | False       | False           | False    |
| QQQ3            | vol_target         |     12.26% |             34.23% |      -26.59% |       78.15% |               77.77% | 1/5                 | False     | True    | True        | False           | False    |
| QQQ3            | sma_underlying_200 |     61.59% |             34.23% |      -43.71% |      119.43% |               77.77% | 2/5                 | True      | True    | True        | False           | False    |
| XS2D            | mean_reversion     |     -0.15% |             22.74% |      -59.35% |       12.87% |               75.08% | 0/5                 | False     | True    | False       | False           | False    |
| XS2D            | momentum           |     12.41% |             22.74% |      -20.95% |       73.56% |               75.08% | 1/5                 | False     | True    | False       | False           | False    |
| XS2D            | vol_target         |     10.18% |             22.74% |      -22.77% |       66.63% |               75.08% | 1/5                 | False     | True    | False       | False           | False    |
| XS2D            | sma_underlying_200 |     31.28% |             22.74% |      -19.38% |      124.28% |               75.08% | 2/5                 | True      | True    | True        | False           | False    |
| 3USL            | mean_reversion     |      2.12% |             23.78% |      -69.31% |       25.70% |               66.91% | 0/5                 | False     | True    | False       | False           | False    |
| 3USL            | momentum           |     17.85% |             23.78% |      -25.16% |       77.04% |               66.91% | 2/5                 | False     | True    | True        | False           | False    |
| 3USL            | vol_target         |      8.66% |             23.78% |      -23.79% |       57.47% |               66.91% | 1/5                 | False     | True    | False       | False           | False    |
| 3USL            | sma_underlying_200 |     44.31% |             23.78% |      -27.86% |      119.14% |               66.91% | 2/5                 | True      | True    | True        | False           | False    |
| HFEA(QQQ3+3BUL) | hfea               |     17.17% |             34.23% |      -69.53% |       60.05% |               77.77% | 1/5                 | False     | True    | False       | False           | False    |
| HFEA(3USL+3BUL) | hfea               |     10.93% |             23.78% |      -55.61% |       48.87% |               66.91% | 1/5                 | False     | True    | False       | False           | False    |


## Dettaglio per sotto-periodo

| asset           | strategy           | period                |    cagr |   max_dd |   sharpe |   n_trades |   cum_return |   buyhold_cum_return | beats_buyhold   |
|:----------------|:-------------------|:----------------------|--------:|---------:|---------:|-----------:|-------------:|---------------------:|:----------------|
| LQQ             | mean_reversion     | 2013-2015             |  16.10% |  -28.97% |   77.20% |         42 |       57.43% |              245.98% | False           |
| LQQ             | mean_reversion     | 2016-2019             |   6.82% |  -30.27% |   39.79% |         58 |       30.72% |              212.99% | False           |
| LQQ             | mean_reversion     | 2020 (crash+recupero) | -17.67% |  -49.45% |  -30.96% |         12 |      -17.99% |               69.45% | False           |
| LQQ             | mean_reversion     | 2021-2022 (bear)      | -30.26% |  -61.03% |  -85.27% |         29 |      -52.12% |              -28.76% | False           |
| LQQ             | mean_reversion     | 2023-oggi             |  25.03% |  -35.75% |  100.87% |         57 |      130.05% |              362.98% | False           |
| LQQ             | momentum           | 2013-2015             |  11.56% |  -32.50% |   60.20% |         49 |       39.45% |              245.98% | False           |
| LQQ             | momentum           | 2016-2019             |   6.74% |  -30.97% |   42.88% |         51 |       30.32% |              212.99% | False           |
| LQQ             | momentum           | 2020 (crash+recupero) |  38.45% |  -22.85% |  109.13% |         13 |       39.35% |               69.45% | False           |
| LQQ             | momentum           | 2021-2022 (bear)      |   9.65% |  -19.96% |   56.14% |         24 |       20.72% |              -28.76% | True            |
| LQQ             | momentum           | 2023-oggi             |  17.36% |  -27.68% |   81.51% |         55 |       81.66% |              362.98% | False           |
| LQQ             | vol_target         | 2013-2015             |  21.96% |  -11.49% |  129.04% |        739 |       82.85% |              245.98% | False           |
| LQQ             | vol_target         | 2016-2019             |  15.01% |  -18.46% |   92.86% |        984 |       76.39% |              212.99% | False           |
| LQQ             | vol_target         | 2020 (crash+recupero) |  21.88% |  -17.36% |  125.20% |        257 |       22.36% |               69.45% | False           |
| LQQ             | vol_target         | 2021-2022 (bear)      |  -2.00% |  -27.73% |   -3.76% |        515 |       -4.04% |              -28.76% | True            |
| LQQ             | vol_target         | 2023-oggi             |  20.67% |  -18.64% |  122.79% |        940 |      101.57% |              362.98% | False           |
| LQQ             | sma_underlying_200 | 2013-2015             |  45.75% |  -21.83% |  148.09% |          7 |      214.25% |              245.98% | False           |
| LQQ             | sma_underlying_200 | 2016-2019             |  31.66% |  -19.31% |  119.59% |         27 |      205.41% |              212.99% | False           |
| LQQ             | sma_underlying_200 | 2020 (crash+recupero) |  68.64% |  -35.23% |  134.94% |          5 |       70.40% |               69.45% | True            |
| LQQ             | sma_underlying_200 | 2021-2022 (bear)      |  18.60% |  -21.69% |   79.49% |          6 |       41.72% |              -28.76% | True            |
| LQQ             | sma_underlying_200 | 2023-oggi             |  46.94% |  -25.14% |  137.14% |          9 |      320.20% |              362.98% | False           |
| QQQ3            | mean_reversion     | 2013-2015             |  38.74% |  -35.83% |  114.44% |         52 |      168.10% |              315.09% | False           |
| QQQ3            | mean_reversion     | 2016-2019             |  15.37% |  -34.88% |   58.79% |         64 |       77.48% |              383.02% | False           |
| QQQ3            | mean_reversion     | 2020 (crash+recupero) | -39.30% |  -62.75% |  -67.66% |         14 |      -39.54% |              123.29% | False           |
| QQQ3            | mean_reversion     | 2021-2022 (bear)      | -41.58% |  -75.79% |  -70.33% |         45 |      -65.79% |              -60.52% | False           |
| QQQ3            | mean_reversion     | 2023-oggi             |  40.42% |  -41.35% |  105.00% |         63 |      250.03% |              745.64% | False           |
| QQQ3            | momentum           | 2013-2015             |  -7.18% |  -53.39% |  -17.55% |         54 |      -20.09% |              315.09% | False           |
| QQQ3            | momentum           | 2016-2019             |  14.15% |  -42.00% |   62.35% |         45 |       70.08% |              383.02% | False           |
| QQQ3            | momentum           | 2020 (crash+recupero) |  84.63% |  -32.46% |  144.92% |         13 |       85.53% |              123.29% | False           |
| QQQ3            | momentum           | 2021-2022 (bear)      |  10.82% |  -27.24% |   50.97% |         18 |       22.76% |              -60.52% | True            |
| QQQ3            | momentum           | 2023-oggi             |   9.60% |  -49.16% |   44.02% |         69 |       40.27% |              745.64% | False           |
| QQQ3            | vol_target         | 2013-2015             |  15.53% |  -11.54% |   94.20% |        746 |       54.45% |              315.09% | False           |
| QQQ3            | vol_target         | 2016-2019             |  18.34% |  -18.51% |  109.55% |       1011 |       96.52% |              383.02% | False           |
| QQQ3            | vol_target         | 2020 (crash+recupero) |  24.43% |  -18.40% |  134.10% |        254 |       24.65% |              123.29% | False           |
| QQQ3            | vol_target         | 2021-2022 (bear)      |  -3.79% |  -26.59% |  -15.12% |        503 |       -7.42% |              -60.52% | True            |
| QQQ3            | vol_target         | 2023-oggi             |  19.04% |  -18.96% |  115.03% |        930 |       90.24% |              745.64% | False           |
| QQQ3            | sma_underlying_200 | 2013-2015             |  32.11% |  -25.02% |   98.13% |          7 |      131.35% |              315.09% | False           |
| QQQ3            | sma_underlying_200 | 2016-2019             |  43.34% |  -36.33% |  114.08% |         27 |      324.00% |              383.02% | False           |
| QQQ3            | sma_underlying_200 | 2020 (crash+recupero) | 175.61% |  -43.71% |  175.66% |          5 |      177.84% |              123.29% | True            |
| QQQ3            | sma_underlying_200 | 2021-2022 (bear)      |  17.76% |  -32.29% |   61.04% |         10 |       38.57% |              -60.52% | True            |
| QQQ3            | sma_underlying_200 | 2023-oggi             |  67.16% |  -34.68% |  128.69% |          9 |      565.94% |              745.64% | False           |
| XS2D            | mean_reversion     | 2013-2015             |  20.33% |  -21.52% |  107.03% |         52 |       74.63% |              104.63% | False           |
| XS2D            | mean_reversion     | 2016-2019             |   4.70% |  -22.58% |   33.93% |         52 |       20.25% |              151.35% | False           |
| XS2D            | mean_reversion     | 2020 (crash+recupero) | -33.92% |  -59.35% |  -84.98% |         18 |      -34.13% |               19.30% | False           |
| XS2D            | mean_reversion     | 2021-2022 (bear)      |  -1.98% |  -37.89% |    7.39% |         33 |       -3.92% |                0.73% | False           |
| XS2D            | mean_reversion     | 2023-oggi             |  13.07% |  -29.51% |   71.67% |         51 |       57.36% |              234.57% | False           |
| XS2D            | momentum           | 2013-2015             |  -0.71% |  -38.34% |    4.15% |         68 |       -2.13% |              104.63% | False           |
| XS2D            | momentum           | 2016-2019             |   3.63% |  -32.69% |   32.18% |         59 |       15.38% |              151.35% | False           |
| XS2D            | momentum           | 2020 (crash+recupero) |  15.56% |  -13.61% |   79.79% |          9 |       15.69% |               19.30% | False           |
| XS2D            | momentum           | 2021-2022 (bear)      |   9.34% |  -16.43% |   59.76% |         16 |       19.52% |                0.73% | True            |
| XS2D            | momentum           | 2023-oggi             |  13.69% |  -16.19% |   81.39% |         57 |       60.58% |              234.57% | False           |
| XS2D            | vol_target         | 2013-2015             |  10.50% |  -12.73% |   70.09% |        642 |       35.07% |              104.63% | False           |
| XS2D            | vol_target         | 2016-2019             |  15.99% |  -21.61% |  103.31% |        684 |       81.30% |              151.35% | False           |
| XS2D            | vol_target         | 2020 (crash+recupero) |   6.56% |  -21.70% |   45.20% |        241 |        6.61% |               19.30% | False           |
| XS2D            | vol_target         | 2021-2022 (bear)      |   1.90% |  -22.77% |   19.60% |        475 |        3.83% |                0.73% | True            |
| XS2D            | vol_target         | 2023-oggi             |  16.41% |  -18.72% |  101.50% |        895 |       75.19% |              234.57% | False           |
| XS2D            | sma_underlying_200 | 2013-2015             |  23.35% |  -13.56% |  113.66% |         18 |       88.14% |              104.63% | False           |
| XS2D            | sma_underlying_200 | 2016-2019             |  21.10% |  -20.32% |  105.34% |         19 |      115.57% |              151.35% | False           |
| XS2D            | sma_underlying_200 | 2020 (crash+recupero) |  41.62% |  -19.38% |  123.45% |         11 |       42.01% |               19.30% | True            |
| XS2D            | sma_underlying_200 | 2021-2022 (bear)      |  22.03% |  -15.61% |  101.30% |         14 |       48.79% |                0.73% | True            |
| XS2D            | sma_underlying_200 | 2023-oggi             |  34.29% |  -17.25% |  140.87% |         19 |      196.82% |              234.57% | False           |
| 3USL            | mean_reversion     | 2013-2015             |  29.80% |  -29.13% |  112.04% |         48 |      119.35% |              168.80% | False           |
| 3USL            | mean_reversion     | 2016-2019             |   7.36% |  -27.86% |   39.45% |         54 |       32.98% |              238.95% | False           |
| 3USL            | mean_reversion     | 2020 (crash+recupero) | -29.63% |  -69.31% |  -26.61% |         22 |      -29.83% |                5.74% | False           |
| 3USL            | mean_reversion     | 2021-2022 (bear)      |  -9.36% |  -61.65% |   -0.59% |         43 |      -17.82% |              -12.03% | False           |
| 3USL            | mean_reversion     | 2023-oggi             |  20.90% |  -38.04% |   78.76% |         51 |      101.44% |              362.73% | False           |
| 3USL            | momentum           | 2013-2015             | -10.97% |  -47.94% |  -52.18% |         56 |      -29.54% |              168.80% | False           |
| 3USL            | momentum           | 2016-2019             |   6.66% |  -44.54% |   42.07% |         53 |       29.53% |              238.95% | False           |
| 3USL            | momentum           | 2020 (crash+recupero) |  16.27% |  -17.93% |   66.71% |          9 |       16.41% |                5.74% | True            |
| 3USL            | momentum           | 2021-2022 (bear)      |  13.74% |  -23.17% |   62.52% |         18 |       29.30% |              -12.03% | True            |
| 3USL            | momentum           | 2023-oggi             |  21.30% |  -25.16% |   91.45% |         57 |      103.95% |              362.73% | False           |
| 3USL            | vol_target         | 2013-2015             |   5.47% |  -15.28% |   41.69% |        691 |       17.40% |              168.80% | False           |
| 3USL            | vol_target         | 2016-2019             |  16.45% |  -24.15% |   99.12% |        961 |       84.24% |              238.95% | False           |
| 3USL            | vol_target         | 2020 (crash+recupero) |   3.76% |  -23.79% |   29.45% |        254 |        3.79% |                5.74% | False           |
| 3USL            | vol_target         | 2021-2022 (bear)      |   1.71% |  -23.25% |   18.50% |        503 |        3.45% |              -12.03% | True            |
| 3USL            | vol_target         | 2023-oggi             |  14.46% |  -20.52% |   89.64% |        930 |       64.62% |              362.73% | False           |
| 3USL            | sma_underlying_200 | 2013-2015             |  15.65% |  -18.20% |   70.83% |         18 |       54.93% |              168.80% | False           |
| 3USL            | sma_underlying_200 | 2016-2019             |  29.73% |  -29.55% |  101.44% |         19 |      184.10% |              238.95% | False           |
| 3USL            | sma_underlying_200 | 2020 (crash+recupero) |  60.79% |  -27.86% |  121.44% |         11 |       61.40% |                5.74% | True            |
| 3USL            | sma_underlying_200 | 2021-2022 (bear)      |  33.45% |  -21.75% |  104.49% |         14 |       77.90% |              -12.03% | True            |
| 3USL            | sma_underlying_200 | 2023-oggi             |  47.04% |  -25.63% |  130.23% |         19 |      314.89% |              362.73% | False           |
| HFEA(QQQ3+3BUL) | hfea               | 2013-2015             |  21.97% |  -20.11% |   82.78% |          3 |       22.45% |              315.09% | False           |
| HFEA(QQQ3+3BUL) | hfea               | 2016-2019             |  32.70% |  -36.83% |  114.33% |          6 |      206.24% |              383.02% | False           |
| HFEA(QQQ3+3BUL) | hfea               | 2020 (crash+recupero) |  83.12% |  -43.62% |  148.83% |          3 |       82.69% |              123.29% | False           |
| HFEA(QQQ3+3BUL) | hfea               | 2021-2022 (bear)      | -32.84% |  -69.53% |  -74.73% |          6 |      -54.61% |              -60.52% | True            |
| HFEA(QQQ3+3BUL) | hfea               | 2023-oggi             |  40.48% |  -39.76% |  115.59% |          8 |      245.91% |              745.64% | False           |
| HFEA(3USL+3BUL) | hfea               | 2013-2015             |   8.81% |  -20.45% |   47.99% |          3 |        8.99% |              168.80% | False           |
| HFEA(3USL+3BUL) | hfea               | 2016-2019             |  25.23% |  -27.81% |  118.13% |          6 |      143.53% |              238.95% | False           |
| HFEA(3USL+3BUL) | hfea               | 2020 (crash+recupero) |  23.71% |  -44.33% |   71.30% |          3 |       23.60% |                5.74% | True            |
| HFEA(3USL+3BUL) | hfea               | 2021-2022 (bear)      | -17.02% |  -55.61% |  -37.79% |          6 |      -30.94% |              -12.03% | False           |
| HFEA(3USL+3BUL) | hfea               | 2023-oggi             |  25.33% |  -33.42% |  102.39% |          8 |      128.02% |              362.73% | False           |