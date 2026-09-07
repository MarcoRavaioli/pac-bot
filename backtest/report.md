# Risultati Fase 2 — Backtest

Soglie di accettazione (Fase 3), fissate prima di eseguire il backtest:

- CAGR out-of-sample (2020-oggi) >= CAGR buy&hold + 2%
- Sharpe out-of-sample non peggiore di buy&hold
- Max drawdown out-of-sample non oltre -75%
- Batte buy&hold in almeno 3/5 sotto-periodi

## Verdetto per asset/strategia (out-of-sample 2020-oggi)

| asset   | strategy       |   oos_cagr |   oos_cagr_buyhold |   oos_max_dd |   oos_sharpe |   oos_sharpe_buyhold | subperiods_beaten   | edge_ok   | dd_ok   | sharpe_ok   | subperiods_ok   | PASSED   |
|:--------|:---------------|-----------:|-------------------:|-------------:|-------------:|---------------------:|:--------------------|:----------|:--------|:------------|:----------------|:---------|
| LQQ     | mean_reversion |     -0.66% |             29.53% |      -66.70% |       13.34% |               82.26% | 0/5                 | False     | True    | False       | False           | False    |
| LQQ     | momentum       |     17.53% |             29.53% |      -27.68% |       78.35% |               82.26% | 1/5                 | False     | True    | False       | False           | False    |
| LQQ     | buy_and_hold   |     29.53% |             29.53% |      -61.21% |       82.26% |               82.26% | 0/5                 | False     | True    | True        | False           | False    |
| QQQ3    | mean_reversion |     -4.80% |             34.23% |      -84.14% |       13.11% |               77.77% | 0/5                 | False     | False   | False       | False           | False    |
| QQQ3    | momentum       |     18.39% |             34.23% |      -49.16% |       65.29% |               77.77% | 1/5                 | False     | True    | False       | False           | False    |
| QQQ3    | buy_and_hold   |     34.23% |             34.23% |      -81.35% |       77.77% |               77.77% | 0/5                 | False     | False   | True        | False           | False    |
| XS2D    | mean_reversion |     -0.15% |             22.74% |      -59.35% |       12.87% |               75.08% | 0/5                 | False     | True    | False       | False           | False    |
| XS2D    | momentum       |     12.41% |             22.74% |      -20.95% |       73.56% |               75.08% | 1/5                 | False     | True    | False       | False           | False    |
| XS2D    | buy_and_hold   |     22.74% |             22.74% |      -59.31% |       75.08% |               75.08% | 0/5                 | False     | True    | True        | False           | False    |
| 3USL    | mean_reversion |      2.12% |             23.78% |      -69.31% |       25.70% |               66.91% | 0/5                 | False     | True    | False       | False           | False    |
| 3USL    | momentum       |     17.85% |             23.78% |      -25.16% |       77.04% |               66.91% | 2/5                 | False     | True    | True        | False           | False    |
| 3USL    | buy_and_hold   |     23.78% |             23.78% |      -76.72% |       66.91% |               66.91% | 0/5                 | False     | False   | True        | False           | False    |


## Dettaglio per sotto-periodo

| asset   | strategy       | period                |    cagr |   max_dd |   sharpe |   n_trades |   win_rate |   cum_return |   buyhold_cum_return | beats_buyhold   |
|:--------|:---------------|:----------------------|--------:|---------:|---------:|-----------:|-----------:|-------------:|---------------------:|:----------------|
| LQQ     | mean_reversion | 2013-2015             |  16.10% |  -28.97% |   77.20% |         42 |     58.88% |       57.43% |              245.98% | False           |
| LQQ     | mean_reversion | 2016-2019             |   6.82% |  -30.27% |   39.79% |         58 |     56.27% |       30.72% |              212.99% | False           |
| LQQ     | mean_reversion | 2020 (crash+recupero) | -17.67% |  -49.45% |  -30.96% |         12 |     54.55% |      -17.99% |               69.45% | False           |
| LQQ     | mean_reversion | 2021-2022 (bear)      | -30.26% |  -61.03% |  -85.27% |         29 |     49.55% |      -52.12% |              -28.76% | False           |
| LQQ     | mean_reversion | 2023-oggi             |  25.03% |  -35.75% |  100.87% |         57 |     57.78% |      130.05% |              362.98% | False           |
| LQQ     | momentum       | 2013-2015             |  11.56% |  -32.50% |   60.20% |         49 |     58.66% |       39.45% |              245.98% | False           |
| LQQ     | momentum       | 2016-2019             |   6.74% |  -30.97% |   42.88% |         51 |     54.63% |       30.32% |              212.99% | False           |
| LQQ     | momentum       | 2020 (crash+recupero) |  38.45% |  -22.85% |  109.13% |         13 |     62.86% |       39.35% |               69.45% | False           |
| LQQ     | momentum       | 2021-2022 (bear)      |   9.65% |  -19.96% |   56.14% |         24 |     58.25% |       20.72% |              -28.76% | True            |
| LQQ     | momentum       | 2023-oggi             |  17.36% |  -27.68% |   81.51% |         55 |     57.07% |       81.66% |              362.98% | False           |
| LQQ     | buy_and_hold   | 2013-2015             |  50.43% |  -29.14% |  144.27% |          1 |     58.69% |      245.98% |              245.98% | False           |
| LQQ     | buy_and_hold   | 2016-2019             |  32.45% |  -40.21% |  102.91% |          1 |     54.50% |      212.99% |              212.99% | False           |
| LQQ     | buy_and_hold   | 2020 (crash+recupero) |  67.72% |  -52.18% |  120.78% |          1 |     61.33% |       69.45% |               69.45% | False           |
| LQQ     | buy_and_hold   | 2021-2022 (bear)      | -15.29% |  -61.21% |  -14.80% |          1 |     53.89% |      -28.76% |              -28.76% | False           |
| LQQ     | buy_and_hold   | 2023-oggi             |  50.81% |  -44.33% |  130.80% |          1 |     56.55% |      362.98% |              362.98% | False           |
| QQQ3    | mean_reversion | 2013-2015             |  38.74% |  -35.83% |  114.44% |         52 |     57.32% |      168.10% |              315.09% | False           |
| QQQ3    | mean_reversion | 2016-2019             |  15.37% |  -34.88% |   58.79% |         64 |     57.33% |       77.48% |              383.02% | False           |
| QQQ3    | mean_reversion | 2020 (crash+recupero) | -39.30% |  -62.75% |  -67.66% |         14 |     52.17% |      -39.54% |              123.29% | False           |
| QQQ3    | mean_reversion | 2021-2022 (bear)      | -41.58% |  -75.79% |  -70.33% |         45 |     47.27% |      -65.79% |              -60.52% | False           |
| QQQ3    | mean_reversion | 2023-oggi             |  40.42% |  -41.35% |  105.00% |         63 |     56.21% |      250.03% |              745.64% | False           |
| QQQ3    | momentum       | 2013-2015             |  -7.18% |  -53.39% |  -17.55% |         54 |     54.91% |      -20.09% |              315.09% | False           |
| QQQ3    | momentum       | 2016-2019             |  14.15% |  -42.00% |   62.35% |         45 |     58.53% |       70.08% |              383.02% | False           |
| QQQ3    | momentum       | 2020 (crash+recupero) |  84.63% |  -32.46% |  144.92% |         13 |     63.82% |       85.53% |              123.29% | False           |
| QQQ3    | momentum       | 2021-2022 (bear)      |  10.82% |  -27.24% |   50.97% |         18 |     57.29% |       22.76% |              -60.52% | True            |
| QQQ3    | momentum       | 2023-oggi             |   9.60% |  -49.16% |   44.02% |         69 |     56.09% |       40.27% |              745.64% | False           |
| QQQ3    | buy_and_hold   | 2013-2015             |  60.41% |  -35.94% |  128.64% |          1 |     55.28% |      315.09% |              315.09% | False           |
| QQQ3    | buy_and_hold   | 2016-2019             |  48.08% |  -55.58% |  107.00% |          1 |     57.43% |      383.02% |              383.02% | False           |
| QQQ3    | buy_and_hold   | 2020 (crash+recupero) | 121.88% |  -70.85% |  135.58% |          1 |     61.26% |      123.29% |              123.29% | False           |
| QQQ3    | buy_and_hold   | 2021-2022 (bear)      | -37.23% |  -81.35% |  -29.10% |          1 |     52.39% |      -60.52% |              -60.52% | False           |
| QQQ3    | buy_and_hold   | 2023-oggi             |  78.34% |  -58.20% |  130.82% |          1 |     56.40% |      745.64% |              745.64% | False           |
| XS2D    | mean_reversion | 2013-2015             |  20.33% |  -21.52% |  107.03% |         52 |     59.47% |       74.63% |              104.63% | False           |
| XS2D    | mean_reversion | 2016-2019             |   4.70% |  -22.58% |   33.93% |         52 |     56.21% |       20.25% |              151.35% | False           |
| XS2D    | mean_reversion | 2020 (crash+recupero) | -33.92% |  -59.35% |  -84.98% |         18 |     56.45% |      -34.13% |               19.30% | False           |
| XS2D    | mean_reversion | 2021-2022 (bear)      |  -1.98% |  -37.89% |    7.39% |         33 |     52.38% |       -3.92% |                0.73% | False           |
| XS2D    | mean_reversion | 2023-oggi             |  13.07% |  -29.51% |   71.67% |         51 |     54.37% |       57.36% |              234.57% | False           |
| XS2D    | momentum       | 2013-2015             |  -0.71% |  -38.34% |    4.15% |         68 |     53.37% |       -2.13% |              104.63% | False           |
| XS2D    | momentum       | 2016-2019             |   3.63% |  -32.69% |   32.18% |         59 |     55.59% |       15.38% |              151.35% | False           |
| XS2D    | momentum       | 2020 (crash+recupero) |  15.56% |  -13.61% |   79.79% |          9 |     62.40% |       15.69% |               19.30% | False           |
| XS2D    | momentum       | 2021-2022 (bear)      |   9.34% |  -16.43% |   59.76% |         16 |     57.98% |       19.52% |                0.73% | True            |
| XS2D    | momentum       | 2023-oggi             |  13.69% |  -16.19% |   81.39% |         57 |     55.66% |       60.58% |              234.57% | False           |
| XS2D    | buy_and_hold   | 2013-2015             |  26.84% |  -21.95% |  108.83% |          1 |     55.28% |      104.63% |              104.63% | False           |
| XS2D    | buy_and_hold   | 2016-2019             |  25.83% |  -33.86% |  105.72% |          1 |     56.24% |      151.35% |              151.35% | False           |
| XS2D    | buy_and_hold   | 2020 (crash+recupero) |  19.14% |  -59.31% |   59.63% |          1 |     59.68% |       19.30% |               19.30% | False           |
| XS2D    | buy_and_hold   | 2021-2022 (bear)      |   0.37% |  -46.01% |   19.64% |          1 |     53.59% |        0.73% |                0.73% | False           |
| XS2D    | buy_and_hold   | 2023-oggi             |  38.71% |  -34.83% |  132.84% |          1 |     55.65% |      234.57% |              234.57% | False           |
| 3USL    | mean_reversion | 2013-2015             |  29.80% |  -29.13% |  112.04% |         48 |     58.74% |      119.35% |              168.80% | False           |
| 3USL    | mean_reversion | 2016-2019             |   7.36% |  -27.86% |   39.45% |         54 |     56.16% |       32.98% |              238.95% | False           |
| 3USL    | mean_reversion | 2020 (crash+recupero) | -29.63% |  -69.31% |  -26.61% |         22 |     56.25% |      -29.83% |                5.74% | False           |
| 3USL    | mean_reversion | 2021-2022 (bear)      |  -9.36% |  -61.65% |   -0.59% |         43 |     50.76% |      -17.82% |              -12.03% | False           |
| 3USL    | mean_reversion | 2023-oggi             |  20.90% |  -38.04% |   78.76% |         51 |     52.81% |      101.44% |              362.73% | False           |
| 3USL    | momentum       | 2013-2015             | -10.97% |  -47.94% |  -52.18% |         56 |     50.56% |      -29.54% |              168.80% | False           |
| 3USL    | momentum       | 2016-2019             |   6.66% |  -44.54% |   42.07% |         53 |     55.21% |       29.53% |              238.95% | False           |
| 3USL    | momentum       | 2020 (crash+recupero) |  16.27% |  -17.93% |   66.71% |          9 |     57.28% |       16.41% |                5.74% | True            |
| 3USL    | momentum       | 2021-2022 (bear)      |  13.74% |  -23.17% |   62.52% |         18 |     57.63% |       29.30% |              -12.03% | True            |
| 3USL    | momentum       | 2023-oggi             |  21.30% |  -25.16% |   91.45% |         57 |     54.46% |      103.95% |              362.73% | False           |
| 3USL    | buy_and_hold   | 2013-2015             |  38.86% |  -32.76% |  107.62% |          1 |     48.55% |      168.80% |              168.80% | False           |
| 3USL    | buy_and_hold   | 2016-2019             |  35.56% |  -47.52% |  101.15% |          1 |     56.04% |      238.95% |              238.95% | False           |
| 3USL    | buy_and_hold   | 2020 (crash+recupero) |   5.69% |  -76.72% |   49.31% |          1 |     56.52% |        5.74% |                5.74% | False           |
| 3USL    | buy_and_hold   | 2021-2022 (bear)      |  -6.22% |  -63.47% |   16.49% |          1 |     53.39% |      -12.03% |              -12.03% | False           |
| 3USL    | buy_and_hold   | 2023-oggi             |  51.45% |  -48.69% |  121.92% |          1 |     54.25% |      362.73% |              362.73% | False           |