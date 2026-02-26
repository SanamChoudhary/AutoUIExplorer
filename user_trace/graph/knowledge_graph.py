"""
Knowledge graph model for tracking navigation patterns.

Wraps a NetworkX DiGraph to store page visits (nodes) and navigation
transitions (edges) with visit/count metadata.
"""

import os
import json

import networkx as nx

from user_trace.graph.url_utils import url_to_feature_id, url_to_name


class KnowledgeGraph:
    """Directed graph of page visits and navigation edges."""

    def __init__(self):
        self.graph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Expose graph properties so callers don't need to reach into .graph
    # ------------------------------------------------------------------
    @property
    def nodes(self):
        return self.graph.nodes

    @property
    def edges(self):
        return self.graph.edges

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------
    def add_page(self, url: str) -> str:
        """Add a URL node to the knowledge graph. Returns the feature ID."""
        feature_id = url_to_feature_id(url)

        if feature_id not in self.graph.nodes:
            self.graph.add_node(
                feature_id,
                id=feature_id,
                name=url_to_name(url),
                url=url,
                visit_count=1
            )
        else:
            # Increment visit count
            self.graph.nodes[feature_id]["visit_count"] += 1

        return feature_id

    def add_edge(self, from_url: str, to_url: str):
        """Add a navigation edge between two URL nodes."""
        from_id = url_to_feature_id(from_url)
        to_id = url_to_feature_id(to_url)

        if from_id != to_id:
            if self.graph.has_edge(from_id, to_id):
                self.graph.edges[from_id, to_id]["count"] += 1
            else:
                self.graph.add_edge(from_id, to_id, relationship="navigated_to", count=1)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, output_path: str) -> str:
        """Save the knowledge graph to a JSON file. Returns the file path."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        graph_data = {
            "nodes": [
                {
                    "id": n,
                    "name": self.graph.nodes[n].get("name", n),
                    "url": self.graph.nodes[n].get("url", ""),
                    "visits": self.graph.nodes[n].get("visit_count", 1)
                }
                for n in self.graph.nodes
            ],
            "edges": [
                {"from": u, "to": v, "count": self.graph.edges[u, v].get("count", 1)}
                for u, v in self.graph.edges
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)

        return output_path
