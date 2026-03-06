CREATE TABLE `spend-sentinel-finops.spend_sentinel.findings`
(
resource_id STRING,
resource_type STRING,
project_id STRING,
labels STRING,
detection_reason STRING,
recommended_action STRING,
confidence_score FLOAT64,
projected_monthly_savings FLOAT64,
detected_at TIMESTAMP
);
