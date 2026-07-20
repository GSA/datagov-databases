from unittest.mock import Mock

from datagov_data_access.search.queries import SearchCriteria
from tests.conftest import make_mock_dataset


def test_search_dataset(opensearch_reader_with_datasets):
    search_criteria = SearchCriteria("test")
    result_obj = opensearch_reader_with_datasets.search(search_criteria)
    assert len(result_obj.results) > 0


def test_index_and_search_other_fields(opensearch_reader_with_datasets):
    # One of the Americorps datasets has tnxs-meph in an identifier
    search_criteria = SearchCriteria("tnxs-meph")
    result_obj = opensearch_reader_with_datasets.search(search_criteria)
    assert len(result_obj.results) > 0


def test_search_spatial_geometry_intersects(opensearch_reader_with_datasets):
    # This point is inside the polygon of the test dataset
    search_criteria = SearchCriteria(
        query="",
        filters={
            "geography": {
                "geometry": {"type": "point", "coordinates": [-75, 40]},
                "within": False,
            }
        },
    )

    result_obj = opensearch_reader_with_datasets.search(search_criteria)

    assert len(result_obj.results) > 0


def test_search_spatial_geometry_within(opensearch_reader_with_datasets):
    # This polygon contains the whole test dataset (and planet)
    search_criteria = SearchCriteria(
        query="",
        filters={
            "geography": {
                "geometry": {
                    "type": "polygon",
                    "coordinates": [
                        [[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]
                    ],
                },
                "within": True,
            }
        },
    )
    result_obj = opensearch_reader_with_datasets.search(search_criteria)

    assert len(result_obj.results) > 0


def test_search_spatial_geometry_intersects_not_within(opensearch_reader_with_datasets):
    # This polygon intersects the test dataset but doesn't contain it
    search_criteria = SearchCriteria(
        query="",
        filters={
            "geography": {
                "geometry": {
                    "type": "polygon",
                    "coordinates": [
                        [[-85, 30], [-85, 40], [-75, 40], [-75, 30], [-85, 30]]
                    ],
                },
                "within": True,
            }
        },
    )
    result_obj = opensearch_reader_with_datasets.search(search_criteria)

    assert len(result_obj.results) == 0

    search_criteria.filters["geography"]["within"] = False

    result_obj = opensearch_reader_with_datasets.search(search_criteria)

    assert len(result_obj.results) > 0


def test_search_collection(opensearch_reader_with_datasets):

    search_criteria = SearchCriteria(
        query="",
        filters={"collection": "https://subdomain.domain/parent/example.shp.iso.xml"},
    )

    result_obj = opensearch_reader_with_datasets.search(search_criteria)

    assert len(result_obj.results) == 2


def test_count_datasets_with_ispartof_passes_filtered_count_query(opensearch_reader):
    """OpenSearch count returns the number of docs matching the supplied query."""
    opensearch_reader.client = Mock()
    opensearch_reader.client.count.return_value = {"count": 7}

    count = opensearch_reader.count_datasets_with_ispartof()

    assert count == 7
    opensearch_reader.client.count.assert_called_once_with(
        index=opensearch_reader.INDEX_NAME,
        body={
            "query": {
                "nested": {
                    "path": "dcat",
                    "query": {"exists": {"field": "dcat.isPartOf"}},
                }
            }
        },
    )


def test_keyword_filter_is_case_insensitive(
    opensearch_reader, opensearch_writer, mock_organization
):
    """
    Searching by lowercase keyword should match a dataset indexed with
    the same keyword in Title Case, and vice versa.
    """

    # Index one dataset whose keyword is stored as "Environment" (Title Case)
    dataset = make_mock_dataset(
        doc_id="kw-case-test-1",
        slug="kw-case-dataset-1",
        keywords=["Environment", "Climate"],
        mock_organization=mock_organization,
    )
    opensearch_writer.index_datasets([dataset])

    search_criteria = SearchCriteria(query="", filters={"keyword": ["environment"]})

    # Filtering with the lowercase form must still find the document.
    result_lower = opensearch_reader.search(search_criteria)
    assert len(result_lower.results) == 1

    # Filtering with the original Title Case form must also work.
    search_criteria.filters["keyword"] = ["Environment"]
    result_title = opensearch_reader.search(search_criteria)
    assert len(result_title.results) == 1

    # An unrelated keyword must return 0.
    search_criteria.filters["keyword"] = ["unrelated"]
    result_none = opensearch_reader.search(search_criteria)
    assert len(result_none.results) == 0


def test_keyword_filter_case_insensitive_mixed_case(
    opensearch_reader, opensearch_writer, mock_organization
):
    """
    Mixed-case filter values must still resolve to the correct
    document regardless of how the keyword was stored.
    """
    dataset = make_mock_dataset(
        doc_id="kw-case-test-mixed",
        slug="kw-case-dataset-mixed",
        keywords=["environment"],
        mock_organization=mock_organization,
    )
    opensearch_writer.index_datasets([dataset])

    # "ENVIRONMENT", "Environment", and "eNvIrOnMeNt" should all match.

    search_criteria = SearchCriteria(query="")

    for variant in ("ENVIRONMENT", "Environment", "eNvIrOnMeNt"):
        search_criteria.filters["keyword"] = [variant]
        result = opensearch_reader.search(search_criteria)
        assert len(result.results) == 1


def test_get_unique_keywords_combines_case_variants(
    opensearch_reader, opensearch_writer, mock_organization
):
    """
    Indexing 'environment' and 'Environment' across two datasets should
    produce a single aggregation bucket with a combined doc_count of 2.
    """
    dataset_lower = make_mock_dataset(
        doc_id="kw-agg-test-1",
        slug="kw-agg-dataset-lower",
        keywords=["environment"],
        mock_organization=mock_organization,
    )
    dataset_title = make_mock_dataset(
        doc_id="kw-agg-test-2",
        slug="kw-agg-dataset-title",
        keywords=["Environment"],
        mock_organization=mock_organization,
    )
    opensearch_writer.index_datasets([dataset_lower, dataset_title])

    keywords = opensearch_reader.get_unique_keywords()

    # Both variants must collapse into one bucket.
    env_buckets = [k for k in keywords if k["keyword"] == "environment"]
    assert len(env_buckets) == 1
    assert env_buckets[0]["count"] == 2


def test_get_unique_keywords_search_filters_by_substring(
    opensearch_reader, opensearch_writer, mock_organization
):
    """
    Passing search="earth science" should return only keyword buckets whose
    normalized value contains that substring, ordered by doc count descending.
    Unrelated keywords must not appear in the results.
    """
    datasets = [
        make_mock_dataset(
            doc_id="kw-search-1",
            slug="kw-search-1",
            keywords=["earth"],
            mock_organization=mock_organization,
        ),
        make_mock_dataset(
            doc_id="kw-search-2",
            slug="kw-search-2",
            keywords=["earth science"],
            mock_organization=mock_organization,
        ),
        make_mock_dataset(
            doc_id="kw-search-3",
            slug="kw-search-3",
            keywords=["earth science > trees"],
            mock_organization=mock_organization,
        ),
        make_mock_dataset(
            doc_id="kw-search-4",
            slug="kw-search-4",
            keywords=["ocean"],
            mock_organization=mock_organization,
        ),
    ]
    opensearch_writer.index_datasets(datasets)

    keywords = opensearch_reader.get_unique_keywords(search="earth science")
    keyword_values = [item["keyword"] for item in keywords]

    assert "earth science" in keyword_values
    assert "earth science > trees" in keyword_values
    # "earth" does not contain the substring "earth science"
    assert "earth" not in keyword_values
    # Completely unrelated keywords must be excluded
    assert "ocean" not in keyword_values


def test_publisher_normalized_field_lowercases_values(
    opensearch_writer, opensearch_reader
):
    document_id = "publisher-normalized-test"
    try:
        opensearch_writer.client.index(
            index=opensearch_writer.INDEX_NAME,
            id=document_id,
            body={"publisher": "ABC"},
            refresh=True,
        )

        response = opensearch_reader.client.search(
            index=opensearch_reader.INDEX_NAME,
            body={
                "query": {
                    "term": {"publisher.normalized": "abc"},
                }
            },
        )

        assert response["hits"]["total"]["value"] == 1
        assert response["hits"]["hits"][0]["_id"] == document_id
    finally:
        opensearch_writer.client.delete(
            index=opensearch_writer.INDEX_NAME,
            id=document_id,
            ignore=[404],
            refresh=True,
        )
