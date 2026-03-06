CREATE TABLE `spend-sentinel-finops.spend_sentinel.actions_log`
(
resource_id STRING,
action_taken STRING,
resource_type STRING,
project_id STRING,
action_timestamp TIMESTAMP,
estimated_savings FLOAT64,
status STRING
);
