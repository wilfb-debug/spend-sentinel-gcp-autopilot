CREATE TABLE `spend-sentinel-finops.spend_sentinel.daily_savings`
(
date DATE,
projected_savings FLOAT64,
actual_savings FLOAT64,
savings_delta FLOAT64,
actions_count INT64
);
