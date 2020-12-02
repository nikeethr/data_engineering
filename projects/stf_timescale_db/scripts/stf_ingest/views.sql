-- view for catchment boundaries
-- TODO: set SRID to global

DROP MATERIALIZED VIEW IF EXISTS view_catchment_boundaries;
CREATE MATERIALIZED VIEW view_catchment_boundaries AS
    SELECT jsonb_build_object(
        'type',     'FeatureCollection',
        'features', jsonb_agg(features.feature)
    )
    FROM (
      SELECT jsonb_build_object(
        'type',       'Feature',
        'id',         catchment,
        'geometry',   ST_AsGeoJSON(geom)::jsonb,
        'properties', to_jsonb(inputs) - 'geom'
    ) AS feature
      FROM (
        SELECT
          ST_Union(geom) AS geom,
          ST_AsGeoJson(ST_Centroid(ST_Union(geom)))::jsonb AS center,
          ST_AsGeoJson(ST_Extent(geom))::jsonb AS bbox,
          catchment
        FROM stf_geom_subcatch
        GROUP BY catchment
      ) AS inputs
    ) AS features;

