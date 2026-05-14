Module 15: Reference Data Service
i.   The system shall provide an authenticated read-only API for querying the geographic reference hierarchy used across all system modules.

ii.   The system shall expose GET /api/ref/regions returning region_id, region_name, and region_code; optionally filtered by region_id.

iii.   The system shall expose GET /api/ref/provinces returning province_id, province_name, and region_id; optionally filtered by region_id.

iv.   The system shall expose GET /api/ref/cities returning city_id, city_name, and province_id; optionally filtered by single province_id or a comma-separated list of province_ids for batch lookup.

v.   All reference data endpoints shall require authentication via any valid WIMS user role.

vi.   Row-level security policies shall restrict visibility so that REGIONAL_ENCODER and REGIONAL_VALIDATOR roles see only reference data for their assigned region; NATIONAL_ANALYST and SYSTEM_ADMIN shall see all regions.

vii.   Reference data shall be sourced exclusively from wims.ref_regions, wims.ref_provinces, and wims.ref_cities; no write operations on reference data shall be exposed through this API.

