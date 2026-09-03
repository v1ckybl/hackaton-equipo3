\set ON_ERROR_STOP on

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS ultima_ventana;

SET search_path TO ultima_ventana, public;

CREATE TABLE source_assets (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_code       text NOT NULL,
    dataset_name        text NOT NULL,
    dataset_version     text NOT NULL DEFAULT 'unspecified',
    external_id         text NOT NULL,
    uri                 text,
    sha256              text,
    coverage_start_at   timestamptz,
    coverage_end_at     timestamptz,
    ingested_at         timestamptz NOT NULL DEFAULT now(),
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_source_asset
        UNIQUE (provider_code, dataset_name, dataset_version, external_id),
    CONSTRAINT ck_source_asset_sha256
        CHECK (sha256 IS NULL OR sha256 ~ '^[0-9A-Fa-f]{64}$'),
    CONSTRAINT ck_source_asset_coverage
        CHECK (
            coverage_start_at IS NULL
            OR coverage_end_at IS NULL
            OR coverage_end_at >= coverage_start_at
        ),
    CONSTRAINT ck_source_asset_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

COMMENT ON TABLE source_assets IS
    'Metadata and checksum for external datasets/files; heavy raster content remains outside PostgreSQL.';

CREATE TABLE pipeline_runs (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_type        text NOT NULL,
    status          text NOT NULL DEFAULT 'RUNNING',
    code_version    text NOT NULL,
    parameters      jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at      timestamptz NOT NULL DEFAULT now(),
    finished_at     timestamptz,
    error_message   text,
    CONSTRAINT ck_pipeline_run_type
        CHECK (run_type IN (
            'INGESTION',
            'SPATIAL_JOIN',
            'FEATURE_BUILD',
            'DATASET_BUILD',
            'INFERENCE'
        )),
    CONSTRAINT ck_pipeline_run_status
        CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
    CONSTRAINT ck_pipeline_run_lifecycle
        CHECK (
            (status = 'RUNNING' AND finished_at IS NULL)
            OR (status IN ('SUCCEEDED', 'FAILED') AND finished_at IS NOT NULL)
        ),
    CONSTRAINT ck_pipeline_run_parameters_object
        CHECK (jsonb_typeof(parameters) = 'object')
);

CREATE TABLE roads (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_asset_id     bigint NOT NULL REFERENCES source_assets(id) ON DELETE RESTRICT,
    source_external_id  text NOT NULL,
    name                text,
    geometry            geometry(MultiLineString, 4326) NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_road_source_feature
        UNIQUE (source_asset_id, source_external_id),
    CONSTRAINT ck_road_geometry_not_empty
        CHECK (NOT ST_IsEmpty(geometry)),
    CONSTRAINT ck_road_geometry_valid
        CHECK (ST_IsValid(geometry))
);

CREATE INDEX ix_roads_geometry_gist ON roads USING gist (geometry);

CREATE TABLE road_segments (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    road_id         bigint NOT NULL REFERENCES roads(id) ON DELETE CASCADE,
    segment_index   integer NOT NULL,
    geometry        geometry(LineString, 4326) NOT NULL,
    length_m        double precision NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_road_segment_index UNIQUE (road_id, segment_index),
    CONSTRAINT ck_road_segment_index_nonnegative CHECK (segment_index >= 0),
    CONSTRAINT ck_road_segment_length_positive CHECK (length_m > 0),
    CONSTRAINT ck_road_segment_geometry_not_empty CHECK (NOT ST_IsEmpty(geometry)),
    CONSTRAINT ck_road_segment_geometry_valid CHECK (ST_IsValid(geometry))
);

CREATE INDEX ix_road_segments_geometry_gist ON road_segments USING gist (geometry);

CREATE TABLE segment_static_features (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id              bigint NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    pipeline_run_id         bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    dem_asset_id            bigint NOT NULL REFERENCES source_assets(id) ON DELETE RESTRICT,
    hydrography_asset_id    bigint REFERENCES source_assets(id) ON DELETE RESTRICT,
    feature_version         text NOT NULL,
    computed_at             timestamptz NOT NULL DEFAULT now(),
    elevation_mean_m        double precision NOT NULL,
    slope_mean_pct          double precision NOT NULL,
    flow_accumulation       double precision,
    distance_to_water_m     double precision,
    road_type               text,
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_static_feature_build
        UNIQUE (segment_id, feature_version, pipeline_run_id),
    CONSTRAINT uq_static_feature_id_segment UNIQUE (id, segment_id),
    CONSTRAINT ck_static_slope_nonnegative CHECK (slope_mean_pct >= 0),
    CONSTRAINT ck_static_flow_nonnegative
        CHECK (flow_accumulation IS NULL OR flow_accumulation >= 0),
    CONSTRAINT ck_static_distance_nonnegative
        CHECK (distance_to_water_m IS NULL OR distance_to_water_m >= 0),
    CONSTRAINT ck_static_metadata_object CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_static_features_segment_time
    ON segment_static_features (segment_id, computed_at DESC);

CREATE TABLE weather_observations (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id          bigint NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    pipeline_run_id     bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    source_asset_id     bigint NOT NULL REFERENCES source_assets(id) ON DELETE RESTRICT,
    observed_at         timestamptz NOT NULL,
    rain_6h_mm          double precision,
    rain_24h_mm         double precision NOT NULL,
    rain_72h_mm         double precision NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_weather_observation
        UNIQUE (segment_id, source_asset_id, observed_at),
    CONSTRAINT uq_weather_observation_id_segment UNIQUE (id, segment_id),
    CONSTRAINT ck_weather_observation_rain_6h
        CHECK (rain_6h_mm IS NULL OR rain_6h_mm >= 0),
    CONSTRAINT ck_weather_observation_rain_24h CHECK (rain_24h_mm >= 0),
    CONSTRAINT ck_weather_observation_rain_72h CHECK (rain_72h_mm >= 0),
    CONSTRAINT ck_weather_observation_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_weather_observations_segment_time
    ON weather_observations (segment_id, observed_at DESC);

CREATE TABLE weather_forecasts (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id              bigint NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    pipeline_run_id         bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    source_asset_id         bigint NOT NULL REFERENCES source_assets(id) ON DELETE RESTRICT,
    issued_at               timestamptz NOT NULL,
    valid_at                timestamptz NOT NULL,
    forecast_rain_3h_mm     double precision,
    forecast_rain_6h_mm     double precision NOT NULL,
    forecast_rain_12h_mm    double precision NOT NULL,
    created_at              timestamptz NOT NULL DEFAULT now(),
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_weather_forecast
        UNIQUE (segment_id, source_asset_id, issued_at, valid_at),
    CONSTRAINT uq_weather_forecast_id_segment UNIQUE (id, segment_id),
    CONSTRAINT ck_weather_forecast_validity CHECK (valid_at >= issued_at),
    CONSTRAINT ck_weather_forecast_rain_3h
        CHECK (forecast_rain_3h_mm IS NULL OR forecast_rain_3h_mm >= 0),
    CONSTRAINT ck_weather_forecast_rain_6h CHECK (forecast_rain_6h_mm >= 0),
    CONSTRAINT ck_weather_forecast_rain_12h CHECK (forecast_rain_12h_mm >= 0),
    CONSTRAINT ck_weather_forecast_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_weather_forecasts_segment_valid_issued
    ON weather_forecasts (segment_id, valid_at, issued_at DESC);

CREATE TABLE satellite_features (
    id                              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id                      bigint NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    pipeline_run_id                 bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    source_asset_id                 bigint NOT NULL REFERENCES source_assets(id) ON DELETE RESTRICT,
    observed_at                     timestamptz NOT NULL,
    vv_backscatter_mean             double precision,
    vh_backscatter_mean             double precision,
    water_coverage_50m_ratio        double precision,
    water_coverage_100m_ratio       double precision NOT NULL,
    water_change_ratio              double precision,
    created_at                      timestamptz NOT NULL DEFAULT now(),
    metadata                        jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_satellite_feature
        UNIQUE (segment_id, source_asset_id, observed_at),
    CONSTRAINT uq_satellite_feature_id_segment UNIQUE (id, segment_id),
    CONSTRAINT ck_satellite_water_50m
        CHECK (
            water_coverage_50m_ratio IS NULL
            OR water_coverage_50m_ratio BETWEEN 0 AND 1
        ),
    CONSTRAINT ck_satellite_water_100m
        CHECK (water_coverage_100m_ratio BETWEEN 0 AND 1),
    CONSTRAINT ck_satellite_water_change
        CHECK (water_change_ratio IS NULL OR water_change_ratio BETWEEN -1 AND 1),
    CONSTRAINT ck_satellite_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_satellite_features_segment_time
    ON satellite_features (segment_id, observed_at DESC);

CREATE TABLE feature_schema_versions (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version                 text NOT NULL UNIQUE,
    feature_order           text[] NOT NULL,
    definition              jsonb NOT NULL,
    definition_checksum     text NOT NULL,
    is_active               boolean NOT NULL DEFAULT false,
    created_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_feature_schema_order_not_empty
        CHECK (cardinality(feature_order) > 0),
    CONSTRAINT ck_feature_schema_definition_object
        CHECK (jsonb_typeof(definition) = 'object')
);

CREATE UNIQUE INDEX uq_feature_schema_one_active
    ON feature_schema_versions ((is_active))
    WHERE is_active;

CREATE TABLE feature_snapshots (
    id                              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id                      bigint NOT NULL REFERENCES road_segments(id) ON DELETE RESTRICT,
    build_run_id                    bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    feature_schema_id               bigint NOT NULL REFERENCES feature_schema_versions(id) ON DELETE RESTRICT,
    as_of_time                      timestamptz NOT NULL,
    prediction_time                 timestamptz NOT NULL,
    generated_at                    timestamptz NOT NULL DEFAULT now(),
    static_feature_id               bigint NOT NULL,
    weather_observation_id          bigint NOT NULL,
    weather_forecast_id             bigint NOT NULL,
    satellite_feature_id            bigint NOT NULL,
    rain_6h_mm                      double precision,
    rain_24h_mm                     double precision NOT NULL,
    rain_72h_mm                     double precision NOT NULL,
    forecast_rain_3h_mm             double precision,
    forecast_rain_6h_mm             double precision NOT NULL,
    forecast_rain_12h_mm            double precision NOT NULL,
    elevation_mean_m                double precision NOT NULL,
    slope_mean_pct                  double precision NOT NULL,
    water_coverage_50m_ratio        double precision,
    water_coverage_100m_ratio       double precision NOT NULL,
    water_change_ratio              double precision,
    vv_backscatter_mean             double precision,
    vh_backscatter_mean             double precision,
    imputation_metadata             jsonb NOT NULL DEFAULT '{}'::jsonb,
    quality_flags                   jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_feature_snapshot_build
        UNIQUE (build_run_id, segment_id, prediction_time),
    CONSTRAINT uq_feature_snapshot_id_segment UNIQUE (id, segment_id),
    CONSTRAINT fk_snapshot_static_feature
        FOREIGN KEY (static_feature_id, segment_id)
        REFERENCES segment_static_features (id, segment_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_snapshot_weather_observation
        FOREIGN KEY (weather_observation_id, segment_id)
        REFERENCES weather_observations (id, segment_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_snapshot_weather_forecast
        FOREIGN KEY (weather_forecast_id, segment_id)
        REFERENCES weather_forecasts (id, segment_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_snapshot_satellite_feature
        FOREIGN KEY (satellite_feature_id, segment_id)
        REFERENCES satellite_features (id, segment_id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_feature_snapshot_horizon CHECK (prediction_time >= as_of_time),
    CONSTRAINT ck_feature_snapshot_rain_6h
        CHECK (rain_6h_mm IS NULL OR rain_6h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_rain_24h CHECK (rain_24h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_rain_72h CHECK (rain_72h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_forecast_3h
        CHECK (forecast_rain_3h_mm IS NULL OR forecast_rain_3h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_forecast_6h CHECK (forecast_rain_6h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_forecast_12h CHECK (forecast_rain_12h_mm >= 0),
    CONSTRAINT ck_feature_snapshot_slope CHECK (slope_mean_pct >= 0),
    CONSTRAINT ck_feature_snapshot_water_50m
        CHECK (
            water_coverage_50m_ratio IS NULL
            OR water_coverage_50m_ratio BETWEEN 0 AND 1
        ),
    CONSTRAINT ck_feature_snapshot_water_100m
        CHECK (water_coverage_100m_ratio BETWEEN 0 AND 1),
    CONSTRAINT ck_feature_snapshot_water_change
        CHECK (water_change_ratio IS NULL OR water_change_ratio BETWEEN -1 AND 1),
    CONSTRAINT ck_feature_snapshot_imputation_object
        CHECK (jsonb_typeof(imputation_metadata) = 'object'),
    CONSTRAINT ck_feature_snapshot_quality_object
        CHECK (jsonb_typeof(quality_flags) = 'object')
);

COMMENT ON TABLE feature_snapshots IS
    'Append-only model input assembled for one road segment and prediction horizon.';

COMMENT ON COLUMN feature_snapshots.as_of_time IS
    'Cutoff time: every dynamic source used by this snapshot must have been available by this instant.';

CREATE INDEX ix_feature_snapshots_segment_prediction
    ON feature_snapshots (segment_id, prediction_time, generated_at DESC);

CREATE INDEX ix_feature_snapshots_schema_prediction
    ON feature_snapshots (feature_schema_id, prediction_time);

CREATE FUNCTION validate_feature_snapshot_lineage()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    observation_time_value   timestamptz;
    satellite_time_value     timestamptz;
    forecast_issued_value    timestamptz;
    forecast_valid_value     timestamptz;
    build_run_type_value     text;
BEGIN
    SELECT run_type
      INTO build_run_type_value
      FROM pipeline_runs
     WHERE id = NEW.build_run_id;

    IF build_run_type_value IS DISTINCT FROM 'FEATURE_BUILD' THEN
        RAISE EXCEPTION 'build_run_id % must reference a FEATURE_BUILD run', NEW.build_run_id;
    END IF;

    SELECT observed_at
      INTO observation_time_value
      FROM weather_observations
     WHERE id = NEW.weather_observation_id;

    IF observation_time_value > NEW.as_of_time THEN
        RAISE EXCEPTION
            'weather observation % occurs after snapshot cutoff %',
            NEW.weather_observation_id,
            NEW.as_of_time;
    END IF;

    SELECT observed_at
      INTO satellite_time_value
      FROM satellite_features
     WHERE id = NEW.satellite_feature_id;

    IF satellite_time_value > NEW.as_of_time THEN
        RAISE EXCEPTION
            'satellite observation % occurs after snapshot cutoff %',
            NEW.satellite_feature_id,
            NEW.as_of_time;
    END IF;

    SELECT issued_at, valid_at
      INTO forecast_issued_value, forecast_valid_value
      FROM weather_forecasts
     WHERE id = NEW.weather_forecast_id;

    IF forecast_issued_value > NEW.as_of_time THEN
        RAISE EXCEPTION
            'forecast % was issued after snapshot cutoff %',
            NEW.weather_forecast_id,
            NEW.as_of_time;
    END IF;

    IF forecast_valid_value IS DISTINCT FROM NEW.prediction_time THEN
        RAISE EXCEPTION
            'forecast % is valid at %, not at prediction time %',
            NEW.weather_forecast_id,
            forecast_valid_value,
            NEW.prediction_time;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_feature_snapshot_lineage
BEFORE INSERT OR UPDATE ON feature_snapshots
FOR EACH ROW
EXECUTE FUNCTION validate_feature_snapshot_lineage();

CREATE FUNCTION prevent_feature_snapshot_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'feature_snapshots are append-only; create a new build run and snapshot instead';
END;
$$;

CREATE TRIGGER trg_prevent_feature_snapshot_mutation
BEFORE UPDATE OR DELETE ON feature_snapshots
FOR EACH ROW
EXECUTE FUNCTION prevent_feature_snapshot_mutation();

CREATE TABLE road_condition_events (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_id          bigint NOT NULL REFERENCES road_segments(id) ON DELETE RESTRICT,
    source_asset_id     bigint REFERENCES source_assets(id) ON DELETE RESTRICT,
    observed_at         timestamptz NOT NULL,
    status              text NOT NULL,
    event_source        text NOT NULL,
    confidence          double precision,
    notes               text,
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_road_condition_status
        CHECK (status IN ('TRANSITABLE', 'DIFFICULT', 'INTRANSITABLE')),
    CONSTRAINT ck_road_condition_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT ck_road_condition_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_road_condition_events_segment_time
    ON road_condition_events (segment_id, observed_at DESC);

CREATE TABLE training_labels (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    feature_snapshot_id     bigint NOT NULL REFERENCES feature_snapshots(id) ON DELETE RESTRICT,
    target_name             text NOT NULL DEFAULT 'intransitable_within_6h',
    target_horizon_hours    integer NOT NULL DEFAULT 6,
    target_value            smallint NOT NULL,
    label_origin            text NOT NULL,
    source_event_id         bigint REFERENCES road_condition_events(id) ON DELETE RESTRICT,
    label_rule_version      text NOT NULL,
    generated_at            timestamptz NOT NULL DEFAULT now(),
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_training_label
        UNIQUE (feature_snapshot_id, target_name, label_rule_version),
    CONSTRAINT uq_training_label_id_snapshot
        UNIQUE (id, feature_snapshot_id),
    CONSTRAINT ck_training_label_horizon CHECK (target_horizon_hours > 0),
    CONSTRAINT ck_training_label_value CHECK (target_value IN (0, 1)),
    CONSTRAINT ck_training_label_origin
        CHECK (label_origin IN ('OBSERVED', 'HEURISTIC', 'SYNTHETIC')),
    CONSTRAINT ck_training_label_observed_source
        CHECK (label_origin <> 'OBSERVED' OR source_event_id IS NOT NULL),
    CONSTRAINT ck_training_label_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE FUNCTION validate_training_label_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    snapshot_segment_value      bigint;
    snapshot_prediction_value   timestamptz;
    event_segment_value         bigint;
    event_time_value            timestamptz;
BEGIN
    IF NEW.source_event_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT segment_id, prediction_time
      INTO snapshot_segment_value, snapshot_prediction_value
      FROM feature_snapshots
     WHERE id = NEW.feature_snapshot_id;

    SELECT segment_id, observed_at
      INTO event_segment_value, event_time_value
      FROM road_condition_events
     WHERE id = NEW.source_event_id;

    IF event_segment_value IS DISTINCT FROM snapshot_segment_value THEN
        RAISE EXCEPTION
            'road condition event % belongs to segment %, snapshot % belongs to segment %',
            NEW.source_event_id,
            event_segment_value,
            NEW.feature_snapshot_id,
            snapshot_segment_value;
    END IF;

    IF event_time_value < snapshot_prediction_value
       OR event_time_value > snapshot_prediction_value
            + make_interval(hours => NEW.target_horizon_hours) THEN
        RAISE EXCEPTION
            'road condition event % is outside the target horizon for snapshot %',
            NEW.source_event_id,
            NEW.feature_snapshot_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_training_label_event
BEFORE INSERT OR UPDATE ON training_labels
FOR EACH ROW
EXECUTE FUNCTION validate_training_label_event();

CREATE TABLE training_datasets (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version                 text NOT NULL UNIQUE,
    feature_schema_id       bigint NOT NULL REFERENCES feature_schema_versions(id) ON DELETE RESTRICT,
    target_name             text NOT NULL,
    target_horizon_hours    integer NOT NULL,
    build_run_id            bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    export_uri              text,
    export_sha256           text,
    parameters              jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_training_dataset_horizon CHECK (target_horizon_hours > 0),
    CONSTRAINT ck_training_dataset_sha256
        CHECK (export_sha256 IS NULL OR export_sha256 ~ '^[0-9A-Fa-f]{64}$'),
    CONSTRAINT ck_training_dataset_parameters_object
        CHECK (jsonb_typeof(parameters) = 'object')
);

CREATE TABLE training_dataset_rows (
    training_dataset_id     bigint NOT NULL REFERENCES training_datasets(id) ON DELETE CASCADE,
    feature_snapshot_id     bigint NOT NULL REFERENCES feature_snapshots(id) ON DELETE RESTRICT,
    training_label_id       bigint NOT NULL,
    split                   text NOT NULL,
    added_at                timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (training_dataset_id, feature_snapshot_id),
    CONSTRAINT uq_training_dataset_label UNIQUE (training_dataset_id, training_label_id),
    CONSTRAINT fk_training_row_label_snapshot
        FOREIGN KEY (training_label_id, feature_snapshot_id)
        REFERENCES training_labels (id, feature_snapshot_id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_training_dataset_split
        CHECK (split IN ('TRAIN', 'VALIDATION', 'TEST'))
);

CREATE FUNCTION validate_training_dataset_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    dataset_schema_value    bigint;
    dataset_target_value    text;
    dataset_horizon_value   integer;
    snapshot_schema_value   bigint;
    label_target_value      text;
    label_horizon_value     integer;
BEGIN
    SELECT feature_schema_id, target_name, target_horizon_hours
      INTO dataset_schema_value, dataset_target_value, dataset_horizon_value
      FROM training_datasets
     WHERE id = NEW.training_dataset_id;

    SELECT feature_schema_id
      INTO snapshot_schema_value
      FROM feature_snapshots
     WHERE id = NEW.feature_snapshot_id;

    SELECT target_name, target_horizon_hours
      INTO label_target_value, label_horizon_value
      FROM training_labels
     WHERE id = NEW.training_label_id;

    IF dataset_schema_value IS DISTINCT FROM snapshot_schema_value THEN
        RAISE EXCEPTION
            'dataset feature schema does not match snapshot feature schema';
    END IF;

    IF dataset_target_value IS DISTINCT FROM label_target_value
       OR dataset_horizon_value IS DISTINCT FROM label_horizon_value THEN
        RAISE EXCEPTION
            'dataset target definition does not match training label definition';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_training_dataset_row
BEFORE INSERT OR UPDATE ON training_dataset_rows
FOR EACH ROW
EXECUTE FUNCTION validate_training_dataset_row();

CREATE TABLE model_versions (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version                 text NOT NULL UNIQUE,
    training_dataset_id     bigint REFERENCES training_datasets(id) ON DELETE RESTRICT,
    feature_schema_id       bigint NOT NULL REFERENCES feature_schema_versions(id) ON DELETE RESTRICT,
    algorithm               text NOT NULL,
    target_name             text NOT NULL,
    target_horizon_hours    integer NOT NULL,
    artifact_uri            text NOT NULL,
    artifact_sha256         text NOT NULL,
    critical_threshold      double precision NOT NULL,
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_model_target_horizon CHECK (target_horizon_hours > 0),
    CONSTRAINT ck_model_artifact_sha256
        CHECK (artifact_sha256 ~ '^[0-9A-Fa-f]{64}$'),
    CONSTRAINT ck_model_critical_threshold
        CHECK (critical_threshold BETWEEN 0 AND 1),
    CONSTRAINT ck_model_metadata_object CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE FUNCTION validate_model_version_contract()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    dataset_schema_value    bigint;
    dataset_target_value    text;
    dataset_horizon_value   integer;
BEGIN
    IF NEW.training_dataset_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT feature_schema_id, target_name, target_horizon_hours
      INTO dataset_schema_value, dataset_target_value, dataset_horizon_value
      FROM training_datasets
     WHERE id = NEW.training_dataset_id;

    IF dataset_schema_value IS DISTINCT FROM NEW.feature_schema_id
       OR dataset_target_value IS DISTINCT FROM NEW.target_name
       OR dataset_horizon_value IS DISTINCT FROM NEW.target_horizon_hours THEN
        RAISE EXCEPTION
            'model contract does not match its training dataset contract';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_model_version_contract
BEFORE INSERT OR UPDATE ON model_versions
FOR EACH ROW
EXECUTE FUNCTION validate_model_version_contract();

CREATE TABLE risk_predictions (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    feature_snapshot_id     bigint NOT NULL REFERENCES feature_snapshots(id) ON DELETE RESTRICT,
    model_version_id        bigint NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    inference_run_id        bigint NOT NULL REFERENCES pipeline_runs(id) ON DELETE RESTRICT,
    risk_score              double precision NOT NULL,
    risk_level              text NOT NULL,
    predicted_at            timestamptz NOT NULL DEFAULT now(),
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_risk_prediction UNIQUE (feature_snapshot_id, model_version_id),
    CONSTRAINT ck_risk_prediction_score CHECK (risk_score BETWEEN 0 AND 1),
    CONSTRAINT ck_risk_prediction_level
        CHECK (risk_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    CONSTRAINT ck_risk_prediction_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX ix_risk_predictions_model_time
    ON risk_predictions (model_version_id, predicted_at DESC);

CREATE FUNCTION validate_risk_prediction_schema()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    snapshot_schema_value   bigint;
    model_schema_value      bigint;
    inference_run_type      text;
BEGIN
    SELECT feature_schema_id
      INTO snapshot_schema_value
      FROM feature_snapshots
     WHERE id = NEW.feature_snapshot_id;

    SELECT feature_schema_id
      INTO model_schema_value
      FROM model_versions
     WHERE id = NEW.model_version_id;

    IF snapshot_schema_value IS DISTINCT FROM model_schema_value THEN
        RAISE EXCEPTION
            'model feature schema does not match feature snapshot schema';
    END IF;

    SELECT run_type
      INTO inference_run_type
      FROM pipeline_runs
     WHERE id = NEW.inference_run_id;

    IF inference_run_type IS DISTINCT FROM 'INFERENCE' THEN
        RAISE EXCEPTION
            'inference_run_id % must reference an INFERENCE run',
            NEW.inference_run_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_risk_prediction_schema
BEFORE INSERT OR UPDATE ON risk_predictions
FOR EACH ROW
EXECUTE FUNCTION validate_risk_prediction_schema();

COMMENT ON TABLE training_labels IS
    'Target values are kept outside feature_snapshots to prevent target leakage during inference.';

COMMENT ON TABLE training_dataset_rows IS
    'Frozen membership and split assignment for a reproducible training dataset.';

COMMIT;
