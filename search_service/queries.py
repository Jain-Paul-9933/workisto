"""
The one hot-path read, as async raw SQL against the SAME Postgres Django owns —
no second ORM (the deliberately narrow boundary from the README). It mirrors the
Django search (increment 5): a GiST-indexed `ST_DWithin` bound, category/mode
matched on a SINGLE offering via EXISTS, ranked by rating then proximity.
"""

_SEARCH_SQL = """
SELECT sp.id,
       sp.full_name,
       sp.bio,
       sp.rating_avg,
       sp.rating_count,
       ST_Distance(
           sp.location,
           ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
       ) AS distance_m
FROM providers_serviceprovider sp
WHERE sp.location IS NOT NULL
  AND sp.accepting_bookings = TRUE
  AND ST_DWithin(
        sp.location,
        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
        $3
  )
  AND EXISTS (
        SELECT 1
        FROM providers_serviceoffering o
        JOIN catalog_servicecategory c ON c.id = o.category_id
        WHERE o.provider_id = sp.id
          AND o.is_active = TRUE
          AND ($4::text IS NULL OR c.slug = $4)
          AND ($5::text IS NULL OR $5 = ANY(o.supported_modes))
  )
ORDER BY sp.rating_avg DESC, distance_m ASC
LIMIT 50
"""


async def search_providers(pool, *, lat, lng, category, mode, radius_km):
    rows = await pool.fetch(
        _SEARCH_SQL, lng, lat, radius_km * 1000.0, category, mode,
    )
    return [
        {
            "id": r["id"],
            "full_name": r["full_name"],
            "bio": r["bio"],
            "rating_avg": float(r["rating_avg"]),
            "rating_count": r["rating_count"],
            "distance_km": round(r["distance_m"] / 1000, 2),
        }
        for r in rows
    ]
