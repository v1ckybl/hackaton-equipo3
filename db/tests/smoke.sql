BEGIN;

SET search_path TO ultima_ventana, extensions, public;

DO $$
DECLARE
    roads_asset_id         bigint;
    dem_asset_id           bigint;
    gpm_asset_id           bigint;
    smn_asset_id           bigint;
    sentinel_asset_id      bigint;
    spatial_run_id         bigint;
    feature_run_id         bigint;
    second_feature_run_id  bigint;
    dataset_run_id         bigint;
    inference_run_id       bigint;
    road_id_value          bigint;
    segment_id_value       bigint;
    second_segment_id      bigint;
    static_feature_id      bigint;
    weather_obs_id         bigint;
    late_weather_obs_id    bigint;
    forecast_id            bigint;
    satellite_feature_id   bigint;
    feature_schema_id      bigint;
    snapshot_id            bigint;
    road_event_id          bigint;
    label_id               bigint;
    dataset_id             bigint;
    model_id               bigint;
    duplicate_rows         integer;
    expected_failure       boolean;
BEGIN
    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'IDECOR', 'rural_roads', '2026-09', 'roads-demo',
        'data/raw/roads/demo.geojson', repeat('1', 64)
    ) RETURNING id INTO roads_asset_id;

    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'IGN', 'MDE-Ar', '2.1', 'dem-demo',
        'data/raw/dem/demo.tif', repeat('2', 64)
    ) RETURNING id INTO dem_asset_id;

    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'NASA_GPM', 'IMERG', '07', 'gpm-demo',
        'data/raw/gpm/demo.nc', repeat('3', 64)
    ) RETURNING id INTO gpm_asset_id;

    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'SMN', 'WRF', '2026-09', 'smn-demo',
        'data/raw/smn/demo.grib2', repeat('4', 64)
    ) RETURNING id INTO smn_asset_id;

    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'SENTINEL1', 'GRD', '2026-09', 'sentinel-demo',
        'data/raw/sentinel/demo.tif', repeat('5', 64)
    ) RETURNING id INTO sentinel_asset_id;

    INSERT INTO pipeline_runs (
        run_type, status, code_version, started_at, finished_at
    ) VALUES (
        'SPATIAL_JOIN', 'SUCCEEDED', 'smoke-v1',
        '2026-09-03 11:00:00+00', '2026-09-03 11:05:00+00'
    ) RETURNING id INTO spatial_run_id;

    INSERT INTO pipeline_runs (
        run_type, status, code_version, started_at, finished_at
    ) VALUES (
        'FEATURE_BUILD', 'SUCCEEDED', 'smoke-v1',
        '2026-09-03 12:00:00+00', '2026-09-03 12:01:00+00'
    ) RETURNING id INTO feature_run_id;

    INSERT INTO pipeline_runs (
        run_type, status, code_version, started_at, finished_at
    ) VALUES (
        'FEATURE_BUILD', 'SUCCEEDED', 'smoke-v1',
        '2026-09-03 12:02:00+00', '2026-09-03 12:03:00+00'
    ) RETURNING id INTO second_feature_run_id;

    INSERT INTO pipeline_runs (
        run_type, status, code_version, started_at, finished_at
    ) VALUES (
        'DATASET_BUILD', 'SUCCEEDED', 'smoke-v1',
        '2026-09-03 20:00:00+00', '2026-09-03 20:01:00+00'
    ) RETURNING id INTO dataset_run_id;

    INSERT INTO pipeline_runs (
        run_type, status, code_version, started_at, finished_at
    ) VALUES (
        'INFERENCE', 'SUCCEEDED', 'smoke-v1',
        '2026-09-03 20:02:00+00', '2026-09-03 20:03:00+00'
    ) RETURNING id INTO inference_run_id;

    INSERT INTO roads (
        source_asset_id, source_external_id, name, geometry
    ) VALUES (
        roads_asset_id,
        'road-27',
        'Camino 27',
        ST_Multi(ST_GeomFromText(
            'LINESTRING(-58.8500 -27.4500, -58.8400 -27.4450)',
            4326
        ))
    ) RETURNING id INTO road_id_value;

    INSERT INTO road_segments (
        road_id, segment_index, geometry, length_m
    ) VALUES (
        road_id_value,
        0,
        ST_GeomFromText(
            'LINESTRING(-58.8500 -27.4500, -58.8450 -27.4475)',
            4326
        ),
        560.0
    ) RETURNING id INTO segment_id_value;

    INSERT INTO road_segments (
        road_id, segment_index, geometry, length_m
    ) VALUES (
        road_id_value,
        1,
        ST_GeomFromText(
            'LINESTRING(-58.8450 -27.4475, -58.8400 -27.4450)',
            4326
        ),
        560.0
    ) RETURNING id INTO second_segment_id;

    INSERT INTO segment_static_features (
        segment_id,
        pipeline_run_id,
        dem_asset_id,
        feature_version,
        computed_at,
        elevation_mean_m,
        slope_mean_pct
    ) VALUES (
        segment_id_value,
        spatial_run_id,
        dem_asset_id,
        'static-v1',
        '2026-09-03 11:05:00+00',
        48.7,
        0.42
    ) RETURNING id INTO static_feature_id;

    INSERT INTO weather_observations (
        segment_id,
        pipeline_run_id,
        source_asset_id,
        observed_at,
        rain_6h_mm,
        rain_24h_mm,
        rain_72h_mm
    ) VALUES (
        segment_id_value,
        spatial_run_id,
        gpm_asset_id,
        '2026-09-03 12:00:00+00',
        14.1,
        61.4,
        138.2
    ) RETURNING id INTO weather_obs_id;

    INSERT INTO weather_observations (
        segment_id,
        pipeline_run_id,
        source_asset_id,
        observed_at,
        rain_6h_mm,
        rain_24h_mm,
        rain_72h_mm
    ) VALUES (
        segment_id_value,
        spatial_run_id,
        gpm_asset_id,
        '2026-09-03 13:00:00+00',
        16.0,
        63.0,
        140.0
    ) RETURNING id INTO late_weather_obs_id;

    INSERT INTO weather_forecasts (
        segment_id,
        pipeline_run_id,
        source_asset_id,
        issued_at,
        valid_at,
        forecast_rain_3h_mm,
        forecast_rain_6h_mm,
        forecast_rain_12h_mm
    ) VALUES (
        segment_id_value,
        spatial_run_id,
        smn_asset_id,
        '2026-09-03 12:00:00+00',
        '2026-09-03 18:00:00+00',
        18.0,
        34.0,
        62.0
    ) RETURNING id INTO forecast_id;

    INSERT INTO satellite_features (
        segment_id,
        pipeline_run_id,
        source_asset_id,
        observed_at,
        vv_backscatter_mean,
        vh_backscatter_mean,
        water_coverage_50m_ratio,
        water_coverage_100m_ratio,
        water_change_ratio
    ) VALUES (
        segment_id_value,
        spatial_run_id,
        sentinel_asset_id,
        '2026-09-02 10:30:00+00',
        -12.5,
        -19.2,
        0.18,
        0.27,
        0.09
    ) RETURNING id INTO satellite_feature_id;

    SELECT id
      INTO feature_schema_id
      FROM feature_schema_versions
     WHERE version = 'v1';

    IF feature_schema_id IS NULL THEN
        RAISE EXCEPTION 'feature schema v1 was not seeded';
    END IF;

    INSERT INTO feature_snapshots (
        segment_id,
        build_run_id,
        feature_schema_id,
        as_of_time,
        prediction_time,
        static_feature_id,
        weather_observation_id,
        weather_forecast_id,
        satellite_feature_id,
        rain_6h_mm,
        rain_24h_mm,
        rain_72h_mm,
        forecast_rain_3h_mm,
        forecast_rain_6h_mm,
        forecast_rain_12h_mm,
        elevation_mean_m,
        slope_mean_pct,
        water_coverage_50m_ratio,
        water_coverage_100m_ratio,
        water_change_ratio,
        vv_backscatter_mean,
        vh_backscatter_mean
    ) VALUES (
        segment_id_value,
        feature_run_id,
        feature_schema_id,
        '2026-09-03 12:00:00+00',
        '2026-09-03 18:00:00+00',
        static_feature_id,
        weather_obs_id,
        forecast_id,
        satellite_feature_id,
        14.1,
        61.4,
        138.2,
        18.0,
        34.0,
        62.0,
        48.7,
        0.42,
        0.18,
        0.27,
        0.09,
        -12.5,
        -19.2
    ) RETURNING id INTO snapshot_id;

    IF (
        SELECT count(*)
          FROM ml_feature_vectors_v1
         WHERE feature_snapshot_id = snapshot_id
           AND rain_24h_mm = 61.4
           AND rain_72h_mm = 138.2
           AND forecast_rain_6h_mm = 34.0
           AND forecast_rain_12h_mm = 62.0
           AND elevation_mean_m = 48.7
           AND slope_mean_pct = 0.42
           AND water_coverage_100m_ratio = 0.27
    ) <> 1 THEN
        RAISE EXCEPTION 'ml_feature_vectors_v1 did not expose the expected vector';
    END IF;

    INSERT INTO road_condition_events (
        segment_id,
        observed_at,
        status,
        event_source,
        confidence
    ) VALUES (
        segment_id_value,
        '2026-09-03 19:00:00+00',
        'INTRANSITABLE',
        'smoke-test',
        0.95
    ) RETURNING id INTO road_event_id;

    INSERT INTO training_labels (
        feature_snapshot_id,
        target_name,
        target_horizon_hours,
        target_value,
        label_origin,
        source_event_id,
        label_rule_version
    ) VALUES (
        snapshot_id,
        'intransitable_within_6h',
        6,
        1,
        'OBSERVED',
        road_event_id,
        'observed-v1'
    ) RETURNING id INTO label_id;

    INSERT INTO training_datasets (
        version,
        feature_schema_id,
        target_name,
        target_horizon_hours,
        build_run_id,
        parameters
    ) VALUES (
        'smoke-dataset-v1',
        feature_schema_id,
        'intransitable_within_6h',
        6,
        dataset_run_id,
        '{"seed": 42}'::jsonb
    ) RETURNING id INTO dataset_id;

    INSERT INTO training_dataset_rows (
        training_dataset_id,
        feature_snapshot_id,
        training_label_id,
        split
    ) VALUES (
        dataset_id,
        snapshot_id,
        label_id,
        'TRAIN'
    );

    IF (
        SELECT count(*)
          FROM ml_training_rows_v1
         WHERE training_dataset_id = dataset_id
           AND feature_snapshot_id = snapshot_id
           AND target_value = 1
           AND split = 'TRAIN'
    ) <> 1 THEN
        RAISE EXCEPTION 'ml_training_rows_v1 did not expose the expected row';
    END IF;

    INSERT INTO model_versions (
        version,
        training_dataset_id,
        feature_schema_id,
        algorithm,
        target_name,
        target_horizon_hours,
        artifact_uri,
        artifact_sha256,
        critical_threshold,
        metadata
    ) VALUES (
        'smoke-model-v1',
        dataset_id,
        feature_schema_id,
        'xgboost',
        'intransitable_within_6h',
        6,
        'models/model_v1.json',
        repeat('a', 64),
        0.70,
        '{"training_dataset": "smoke-dataset-v1"}'::jsonb
    ) RETURNING id INTO model_id;

    INSERT INTO risk_predictions (
        feature_snapshot_id,
        model_version_id,
        inference_run_id,
        risk_score,
        risk_level
    ) VALUES (
        snapshot_id,
        model_id,
        inference_run_id,
        0.78,
        'CRITICAL'
    );

    INSERT INTO source_assets (
        provider_code, dataset_name, dataset_version, external_id, uri, sha256
    ) VALUES (
        'IDECOR', 'rural_roads', '2026-09', 'roads-demo',
        'data/raw/roads/demo.geojson', repeat('1', 64)
    ) ON CONFLICT (provider_code, dataset_name, dataset_version, external_id)
      DO NOTHING;

    GET DIAGNOSTICS duplicate_rows = ROW_COUNT;
    IF duplicate_rows <> 0 THEN
        RAISE EXCEPTION 'source asset idempotency constraint did not prevent a duplicate';
    END IF;

    expected_failure := false;
    BEGIN
        INSERT INTO satellite_features (
            segment_id,
            pipeline_run_id,
            source_asset_id,
            observed_at,
            water_coverage_100m_ratio
        ) VALUES (
            segment_id_value,
            spatial_run_id,
            sentinel_asset_id,
            '2026-09-01 10:30:00+00',
            1.2
        );
    EXCEPTION WHEN OTHERS THEN
        expected_failure := true;
    END;
    IF NOT expected_failure THEN
        RAISE EXCEPTION 'out-of-range water coverage was accepted';
    END IF;

    expected_failure := false;
    BEGIN
        INSERT INTO feature_snapshots (
            segment_id,
            build_run_id,
            feature_schema_id,
            as_of_time,
            prediction_time,
            static_feature_id,
            weather_observation_id,
            weather_forecast_id,
            satellite_feature_id,
            rain_24h_mm,
            rain_72h_mm,
            forecast_rain_6h_mm,
            forecast_rain_12h_mm,
            elevation_mean_m,
            slope_mean_pct,
            water_coverage_100m_ratio
        ) VALUES (
            segment_id_value,
            second_feature_run_id,
            feature_schema_id,
            '2026-09-03 12:00:00+00',
            '2026-09-03 18:00:00+00',
            static_feature_id,
            late_weather_obs_id,
            forecast_id,
            satellite_feature_id,
            63.0,
            140.0,
            34.0,
            62.0,
            48.7,
            0.42,
            0.27
        );
    EXCEPTION WHEN OTHERS THEN
        expected_failure := true;
    END;
    IF NOT expected_failure THEN
        RAISE EXCEPTION 'snapshot accepted an observation newer than as_of_time';
    END IF;

    expected_failure := false;
    BEGIN
        INSERT INTO feature_snapshots (
            segment_id,
            build_run_id,
            feature_schema_id,
            as_of_time,
            prediction_time,
            static_feature_id,
            weather_observation_id,
            weather_forecast_id,
            satellite_feature_id,
            rain_24h_mm,
            rain_72h_mm,
            forecast_rain_6h_mm,
            forecast_rain_12h_mm,
            elevation_mean_m,
            slope_mean_pct,
            water_coverage_100m_ratio
        ) VALUES (
            second_segment_id,
            second_feature_run_id,
            feature_schema_id,
            '2026-09-03 12:00:00+00',
            '2026-09-03 18:00:00+00',
            static_feature_id,
            weather_obs_id,
            forecast_id,
            satellite_feature_id,
            61.4,
            138.2,
            34.0,
            62.0,
            48.7,
            0.42,
            0.27
        );
    EXCEPTION WHEN OTHERS THEN
        expected_failure := true;
    END;
    IF NOT expected_failure THEN
        RAISE EXCEPTION 'snapshot accepted lineage from another segment';
    END IF;

    expected_failure := false;
    BEGIN
        UPDATE feature_snapshots
           SET quality_flags = '{"modified": true}'::jsonb
         WHERE id = snapshot_id;
    EXCEPTION WHEN OTHERS THEN
        expected_failure := true;
    END;
    IF NOT expected_failure THEN
        RAISE EXCEPTION 'append-only snapshot accepted an update';
    END IF;
END;
$$;

ROLLBACK;

SELECT 'ultima_ventana database smoke test: OK' AS result;
