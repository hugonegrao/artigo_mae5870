# ARIMAX Model Analysis

## Model specification

The selected ARIMAX model was an ARIMA model with calendar-based exogenous regressors. The final specification was:

```text
ARIMAX(2, 1, 2)
```

The model was fitted using the training period from 2018-01-01 to 2024-12-31 and evaluated strictly on the test period from 2025-01-01 to 2025-12-31.

The exogenous variables used in the ARIMAX model were known calendar variables:

- day of week
- month
- quarter
- weekend indicator
- holiday indicator
- holiday eve indicator
- post-holiday indicator
- beginning-of-month indicator
- end-of-month indicator
- annual Fourier terms

These variables are known in advance for the forecast horizon, so their use does not imply data leakage.

## Model selection

The ARIMAX order was selected through a systematic search over non-seasonal ARIMA candidates:

```text
p = 0, 1, 2
d = 0, 1
q = 0, 1, 2
```

For each candidate, the same set of calendar exogenous variables was included. Candidate models were ranked by AIC and BIC. The best ARIMAX candidate was:

```text
order = (2, 1, 2)
AIC   = 44315.69
BIC   = 44537.80
```

The next closest ARIMAX candidate was ARIMAX(1, 1, 2), with AIC = 44322.79. Thus, ARIMAX(2, 1, 2) was selected as the best non-seasonal model with exogenous calendar effects.

## Forecast performance

The ARIMAX model obtained the best predictive performance among all evaluated models on the 2025 test set:

```text
MAE  = 2811.07
RMSE = 3788.66
MAPE = 3.41%
```

Compared with the baseline models, ARIMAX showed a substantial improvement:

```text
Naive forecast:
RMSE = 10456.25
MAPE = 10.70%

Seasonal naive forecast:
RMSE = 9910.79
MAPE = 9.44%

ARIMAX:
RMSE = 3788.66
MAPE = 3.41%
```

This result indicates that the inclusion of calendar regressors and the ARIMA error structure substantially improved out-of-sample forecasting accuracy.

## Interpretation of calendar effects

The most statistically significant calendar effects were associated with weekends, holidays and day-of-week patterns.

The holiday coefficient was strongly negative:

```text
is_holiday = -7604.15
```

This suggests that national holidays are associated with a marked reduction in daily energy load, conditional on the autoregressive structure and the other calendar controls.

The weekend indicator was also strongly negative:

```text
is_weekend = -4584.75
```

This is consistent with lower economic and industrial activity during weekends.

The holiday eve and post-holiday effects were also significant:

```text
is_holiday_eve  = -1718.01
is_post_holiday = -1688.89
```

These effects suggest that demand reductions are not limited to the holiday itself, but may extend to adjacent days.

The annual Fourier term `annual_cos_1` was statistically significant:

```text
annual_cos_1 = 3687.76
```

This indicates the presence of a smooth annual seasonal component not fully captured by monthly dummy variables alone.

## Autoregressive structure

The AR and MA terms were also statistically significant:

```text
ar.L1 =  0.9770
ar.L2 = -0.2154
ma.L1 = -0.9246
```

This confirms that the daily load series has strong temporal dependence even after first differencing and after controlling for calendar effects.

## Residual diagnostics

The Ljung-Box test for the ARIMAX residuals produced statistically significant p-values at the evaluated lags:

```text
lag  7: p-value = 6.38e-10
lag 14: p-value = 1.22e-07
lag 21: p-value = 2.65e-06
lag 28: p-value = 5.28e-05
```

Therefore, the null hypothesis of no residual autocorrelation is rejected. This means that the ARIMAX residuals are not perfect white noise.

However, the ARIMAX model still achieved the best out-of-sample forecast accuracy among the evaluated candidates. Thus, the model selection should be interpreted as a balance between predictive performance and residual adequacy. The residual diagnostics suggest that additional structure could still be explored in future work, especially more flexible seasonal dynamics or alternative specifications for short-term dependence.

## Final assessment

The ARIMAX(2, 1, 2) model is recommended as the final forecasting model for the article because it achieved the best predictive performance on the 2025 test set while maintaining a statistically interpretable structure.

The model captures:

- strong short-term temporal dependence
- calendar effects related to weekdays and weekends
- reductions in demand on holidays and adjacent days
- smooth annual seasonality through Fourier terms

Although residual autocorrelation remains, the model provides the best empirical balance between accuracy, interpretability and methodological rigor among the evaluated alternatives.
