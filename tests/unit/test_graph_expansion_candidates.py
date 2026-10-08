from poldergraph.models.edge import Edge, EdgeType, Provenance
from poldergraph.retrieval.lexical import Candidate
from poldergraph.retrieval.service import QueryService, SearchFilters
from poldergraph.storage.repository import Repository


def test_graph_neighbors_are_ranked_candidates_with_evidence(indexed_workspace, monkeypatch):
    import poldergraph.retrieval.service as service_module

    repo = Repository(indexed_workspace.con)
    entities = repo.con.execute(
        "SELECT id FROM entities WHERE root_id=? ORDER BY id LIMIT 2",
        (indexed_workspace.root_id(),),
    ).fetchall()
    assert len(entities) == 2
    seed_id, neighbor_id = (row[0] for row in entities)
    seed = repo.get_entity(seed_id)
    neighbor = repo.get_entity(neighbor_id)
    repo.upsert_edges([Edge(
        source_id=seed_id,
        target_id=neighbor_id,
        type=EdgeType.CALLS,
        provenance=Provenance.EXTRACTED,
        source_location={"path": seed.path, "line": 7},
    )])

    monkeypatch.setattr(service_module, "exact_matches", lambda *_a, **_k: [
        Candidate(entity_id=seed_id, entity=seed, features={"exact_name": 1.0}, channels={"exact_name"})
    ])
    monkeypatch.setattr(service_module, "lexical_candidates", lambda *_a, **_k: [])
    monkeypatch.setattr(service_module, "semantic_candidates", lambda *_a, **_k: ([], None))
    service = QueryService(repo, indexed_workspace.config, root_id=indexed_workspace.root_id())

    lexical_only = service.search("seed", include_semantic=False)
    assert neighbor_id not in {item.entity_id for item in lexical_only.results}

    expanded = service.search("seed", include_semantic=False, include_structural_context=True)
    found = next(item for item in expanded.results if item.entity_id == neighbor_id)
    payload = next(item for item in expanded.to_dict()["results"] if item["id"] == neighbor_id)
    assert found.entity.id == neighbor.id
    assert found.graph_provenance["seed_id"] == seed_id
    assert found.graph_provenance["distance"] == 1
    assert found.graph_provenance["provenances"] == ["extracted"]
    assert payload["evidence"] == "graph-expanded"
    assert payload["graph_provenance"]["path"][0]["source_location"]["line"] == 7

    excluded = service.search(
        "seed", include_semantic=False, include_structural_context=True,
        filters=SearchFilters(provenances=["inferred"]),
    )
    assert neighbor_id not in {item.entity_id for item in excluded.results}
