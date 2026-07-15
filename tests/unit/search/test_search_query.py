from datagov_data_access.search.queries.registry import build_sort_clause


def test_relevance_sort_uses_popularity_tie_breaker():

    sort_clause = build_sort_clause(sort_by="relevance")

    assert sort_clause == [
        {"_score": {"order": "desc"}},
        {"popularity": {"order": "desc", "missing": "_last"}},
        {"_id": {"order": "desc"}},
    ]


def test_distance_sort_uses_geo_distance():
    sort_clause = build_sort_clause(
        sort_by="distance", sort_point={"lat": 40.0, "lon": -75.0}
    )

    assert sort_clause[0]["_geo_distance"]["spatial_centroid"] == {
        "lat": 40.0,
        "lon": -75.0,
    }
    assert sort_clause[0]["_geo_distance"]["order"] == "asc"


def test_last_harvested_date_sort_uses_latest_first():
    sort_clause = build_sort_clause(sort_by="last_harvested_date")

    assert sort_clause == [
        {"last_harvested_date": {"order": "desc", "missing": "_last"}},
        {"_score": {"order": "desc"}},
        {"popularity": {"order": "desc", "missing": "_last"}},
        {"_id": {"order": "desc"}},
    ]
