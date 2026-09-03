BEGIN;

SET search_path TO ultima_ventana, extensions, public;

WITH schema_definition AS (
    SELECT jsonb_build_object(
        'version', 'v1',
        'target', jsonb_build_object(
            'name', 'intransitable_within_6h',
            'type', 'binary',
            'horizon_hours', 6
        ),
        'time_contract', jsonb_build_object(
            'as_of_time', 'latest instant at which a source may have been available',
            'prediction_time', 'future instant represented by the feature vector',
            'forecast_selection', 'issued_at <= as_of_time and valid_at = prediction_time'
        ),
        'features', jsonb_build_array(
            jsonb_build_object(
                'position', 1,
                'name', 'rain_24h_mm',
                'type', 'float64',
                'unit', 'mm',
                'nullable', false,
                'description', 'Observed precipitation accumulated over the trailing 24 hours.'
            ),
            jsonb_build_object(
                'position', 2,
                'name', 'rain_72h_mm',
                'type', 'float64',
                'unit', 'mm',
                'nullable', false,
                'description', 'Observed precipitation accumulated over the trailing 72 hours.'
            ),
            jsonb_build_object(
                'position', 3,
                'name', 'forecast_rain_6h_mm',
                'type', 'float64',
                'unit', 'mm',
                'nullable', false,
                'description', 'Provider-normalized six-hour forecast accumulation for the prediction horizon.'
            ),
            jsonb_build_object(
                'position', 4,
                'name', 'forecast_rain_12h_mm',
                'type', 'float64',
                'unit', 'mm',
                'nullable', false,
                'description', 'Provider-normalized twelve-hour forecast accumulation for the prediction horizon.'
            ),
            jsonb_build_object(
                'position', 5,
                'name', 'elevation_mean_m',
                'type', 'float64',
                'unit', 'm',
                'nullable', false,
                'description', 'Mean elevation inside the road segment analysis geometry.'
            ),
            jsonb_build_object(
                'position', 6,
                'name', 'slope_mean_pct',
                'type', 'float64',
                'unit', 'percent',
                'nullable', false,
                'description', 'Mean terrain slope expressed as a percentage.'
            ),
            jsonb_build_object(
                'position', 7,
                'name', 'water_coverage_100m_ratio',
                'type', 'float64',
                'unit', 'ratio',
                'nullable', false,
                'description', 'Estimated water coverage ratio inside the 100 metre segment buffer.'
            )
        ),
        'optional_snapshot_features', jsonb_build_array(
            'rain_6h_mm',
            'forecast_rain_3h_mm',
            'water_coverage_50m_ratio',
            'water_change_ratio',
            'vv_backscatter_mean',
            'vh_backscatter_mean'
        )
    ) AS definition
)
INSERT INTO feature_schema_versions (
    version,
    feature_order,
    definition,
    definition_checksum,
    is_active
)
SELECT
    'v1',
    ARRAY[
        'rain_24h_mm',
        'rain_72h_mm',
        'forecast_rain_6h_mm',
        'forecast_rain_12h_mm',
        'elevation_mean_m',
        'slope_mean_pct',
        'water_coverage_100m_ratio'
    ]::text[],
    definition,
    md5(definition::text),
    true
FROM schema_definition
ON CONFLICT (version) DO NOTHING;

CREATE OR REPLACE VIEW ml_feature_vectors_v1 AS
SELECT
    snapshot.id AS feature_snapshot_id,
    snapshot.segment_id,
    snapshot.as_of_time,
    snapshot.prediction_time,
    snapshot.rain_24h_mm,
    snapshot.rain_72h_mm,
    snapshot.forecast_rain_6h_mm,
    snapshot.forecast_rain_12h_mm,
    snapshot.elevation_mean_m,
    snapshot.slope_mean_pct,
    snapshot.water_coverage_100m_ratio
FROM feature_snapshots AS snapshot
JOIN feature_schema_versions AS schema_version
  ON schema_version.id = snapshot.feature_schema_id
WHERE schema_version.version = 'v1';

COMMENT ON VIEW ml_feature_vectors_v1 IS
    'Stable inference contract. Select the seven feature columns explicitly and in the documented order.';

CREATE OR REPLACE VIEW ml_training_rows_v1 AS
SELECT
    dataset.id AS training_dataset_id,
    dataset.version AS training_dataset_version,
    dataset_row.split,
    snapshot.id AS feature_snapshot_id,
    snapshot.segment_id,
    snapshot.as_of_time,
    snapshot.prediction_time,
    snapshot.rain_24h_mm,
    snapshot.rain_72h_mm,
    snapshot.forecast_rain_6h_mm,
    snapshot.forecast_rain_12h_mm,
    snapshot.elevation_mean_m,
    snapshot.slope_mean_pct,
    snapshot.water_coverage_100m_ratio,
    label.target_name,
    label.target_horizon_hours,
    label.target_value,
    label.label_origin,
    label.label_rule_version
FROM training_dataset_rows AS dataset_row
JOIN training_datasets AS dataset
  ON dataset.id = dataset_row.training_dataset_id
JOIN feature_snapshots AS snapshot
  ON snapshot.id = dataset_row.feature_snapshot_id
JOIN feature_schema_versions AS schema_version
  ON schema_version.id = snapshot.feature_schema_id
JOIN training_labels AS label
  ON label.id = dataset_row.training_label_id
WHERE schema_version.version = 'v1'
  AND dataset.feature_schema_id = snapshot.feature_schema_id;

COMMENT ON VIEW ml_training_rows_v1 IS
    'Reproducible v1 training rows with frozen split and target stored separately from inference features.';

REVOKE ALL ON ml_feature_vectors_v1, ml_training_rows_v1
    FROM PUBLIC, anon, authenticated, service_role;

COMMIT;
