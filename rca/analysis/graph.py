"""Build a directed causal graph from causality test results."""

import networkx as nx


def build_causal_graph(causal_edges: list[dict]) -> nx.DiGraph:
    """Build a directed causal graph from causality analysis results."""
    graph = nx.DiGraph()
    for edge in causal_edges:
        cause = edge.get("cause")
        effect = edge.get("effect")
        confidence = float(edge.get("confidence", 0))
        graph.add_edge(cause, effect, weight=confidence)
    return graph


def identify_root_causes(graph: nx.DiGraph) -> list[dict]:
    """Identify root cause nodes with zero in-degree (or minimum in-degree)."""
    candidates = [n for n in graph.nodes if graph.in_degree(n) == 0]
    if not candidates:
        min_in_deg = min(dict(graph.in_degree()).values(), default=0)
        candidates = [n for n in graph.nodes if graph.in_degree(n) == min_in_deg]

    root_analysis: list[dict] = []
    for node in candidates:
        out_edges = list(graph.out_edges(node, data=True))
        out_degree = len(out_edges)
        causes = [edge[1] for edge in out_edges]
        total_weight = sum(float(data.get("weight", 0)) for _, _, data in out_edges)
        score = (out_degree * 2) + total_weight
        root_analysis.append(
            {
                "service_metric": node,
                "score": score,
                "out_degree": out_degree,
                "causes": causes,
            }
        )

    return sorted(root_analysis, key=lambda item: item["score"], reverse=True)
