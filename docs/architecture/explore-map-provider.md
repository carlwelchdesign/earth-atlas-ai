# Explore map-provider configuration

EAT-018 keeps map rendering, geocoding, catalog search, and deterministic processing independent. The hosted private R&D configuration selects MapTiler Cloud for the basemap and explicit place-name resolution. Local development falls back to bounded public OpenStreetMap services.

## Deployment matrix

| Surface | Local development fallback | Private R&D deployment |
| --- | --- | --- |
| MapLibre style | Public OpenStreetMap raster tiles | MapTiler Dataviz style |
| Explicit place names | OpenStreetMap Nominatim | MapTiler Geocoding |
| Latitude/longitude | Local browser calculation | Local browser calculation |
| Credentials | None | Restricted MapTiler API key |
| Intended use | Local owner review only | Private non-commercial/R&D hosting |

Set both variables for a consistent private R&D deployment:

```sh
export ECHOATLAS_MAPTILER_API_KEY="restricted-server-key" # pragma: allowlist secret
export VITE_MAPTILER_API_KEY="restricted-public-map-key" # pragma: allowlist secret
```

The backend variable selects the allowlisted `https://api.maptiler.com/geocoding` adapter. The Vite variable selects the MapTiler Dataviz style in MapLibre. A frontend map key is necessarily visible to the browser; restrict it by allowed origin and permitted APIs in MapTiler. Never commit either value. A deployment that omits both variables visibly identifies the public OSM development fallback.

Place names leave the browser only after an explicit **Go** action. Coordinate searches are parsed and bounded locally. The backend validates query length, HTTPS host and redirects, response size, timeout, schema, coordinate ranges, and result count before returning a fixed 0.15° × 0.15° AOI. Provider payloads and credentials do not enter UI state or the deterministic processing domain.

## Terms, capacity, and release boundary

As reviewed on 2026-08-25, MapTiler's Free plan supports testing, personal/non-commercial use, and commercial-product R&D, requires no billing information, pauses at the plan quota, and provides no production SLA. That fits EchoAtlas's current private R&D status. It does not authorize a public or commercial launch.

Before public or commercial deployment, the owner must approve one of:

1. a suitable MapTiler subscription and spending/usage controls;
2. another provider implemented behind the same adapters; or
3. a self-hosted OSM-derived stack with documented storage, updates, caching, availability, privacy, and operating cost.

Current references:

- [MapTiler Cloud pricing](https://www.maptiler.com/cloud/pricing/)
- [MapTiler Cloud terms](https://www.maptiler.com/terms/cloud/)
- [MapTiler geocoding API](https://docs.maptiler.com/cloud/api/geocoding/)
- [MapTiler API-key guidance](https://docs.maptiler.com/cloud/api/authentication-key/)
- [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/)
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
