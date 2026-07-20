from datagov_data_access.db.interfaces.catalog import CatalogDBInterface

"""
the input interface fixtures used in these tests are an HarvesterDBInterface instance
but the tests expect a CatalogDBInterface instance so passing the db session in the 
harvester interface instance to the catalog interface
"""


def test_get_organizations_includes_zero_dataset_orgs_with_opensearch_counts(
    interface_with_organization, monkeypatch
):
    catalog_interface = CatalogDBInterface(session=interface_with_organization.db)
    monkeypatch.setattr(
        catalog_interface.opensearch,
        "get_organization_counts",
        lambda size: [{"slug": "test-org", "count": 4}],
    )

    organizations = catalog_interface.get_organizations()

    # Organizations with datasets are listed first, so the org with a count
    # from OpenSearch sorts to the top.
    assert organizations[0]["slug"] == "test-org"

    by_slug = {org["slug"]: org for org in organizations}
    assert by_slug["test-org"]["dataset_count"] == 4
    # Organizations with no datasets are still included with a zero count.
    assert by_slug["test-org-filtered"]["dataset_count"] == 0


def test_get_organizations_db_fallback_includes_zero_dataset_orgs(
    interface_with_dataset, monkeypatch
):
    def _raise(_size):
        raise RuntimeError("OpenSearch unavailable")

    catalog_interface = CatalogDBInterface(session=interface_with_dataset.db)
    monkeypatch.setattr(catalog_interface.opensearch, "get_organization_counts", _raise)

    organizations = catalog_interface.get_organizations()
    by_slug = {org["slug"]: org for org in organizations}

    assert by_slug["test-org"]["dataset_count"] > 0
    # Organizations with no datasets are still included with a zero count.
    assert by_slug["test-org-filtered"]["dataset_count"] == 0


def test_get_top_publishers_returns_top_100(interface_with_dataset, monkeypatch):
    captured_size = None

    def _get_publisher_counts(size):
        nonlocal captured_size
        captured_size = size
        return [
            {"name": "Agency Delta", "count": 3},
            {"name": "Agency Beta", "count": 1},
            {"name": "Agency Gamma", "count": 2},
            {"name": "Agency Alpha", "count": 1},
        ]

    catalog_interface = CatalogDBInterface(session=interface_with_dataset.db)
    monkeypatch.setattr(
        catalog_interface.opensearch,
        "get_publisher_counts",
        _get_publisher_counts,
    )

    publishers = catalog_interface.get_top_publishers()

    assert captured_size == 100
    assert publishers == [
        {"name": "Agency Delta", "count": 3},
        {"name": "Agency Gamma", "count": 2},
        {"name": "Agency Alpha", "count": 1},
        {"name": "Agency Beta", "count": 1},
    ]
