"""
Knowledge graph visualization using matplotlib.

Renders the navigation graph as a node-link diagram, saves it as a PNG,
and displays it interactively.
"""

import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

from user_trace.ui.console import Colors, colored


def visualize_knowledge_graph(graph: nx.DiGraph, output_dir: str):
    """Display and save the knowledge graph using matplotlib.

    Args:
        graph: A NetworkX DiGraph with 'visit_count' on nodes and 'count' on edges.
        output_dir: Directory where the PNG image will be saved.
    """
    if len(graph.nodes) == 0:
        return

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.suptitle('Knowledge Graph - Navigation Map', fontsize=16, fontweight='bold')

    # Choose layout based on graph size
    if len(graph.nodes) <= 5:
        pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
    else:
        pos = nx.kamada_kawai_layout(graph)

    # Color nodes by visit count
    visit_counts = [graph.nodes[n].get('visit_count', 1) for n in graph.nodes]
    max_visits = max(visit_counts) if visit_counts else 1
    node_colors = [plt.cm.Blues(0.3 + 0.7 * (v / max_visits)) for v in visit_counts]

    # Size nodes by visit count
    node_sizes = [800 + 400 * (v / max_visits) for v in visit_counts]

    # Draw edges with arrows
    edge_counts = [graph.edges[u, v].get('count', 1) for u, v in graph.edges]
    max_edge_count = max(edge_counts) if edge_counts else 1
    edge_widths = [1 + 2 * (c / max_edge_count) for c in edge_counts]

    nx.draw_networkx_edges(
        graph, pos, ax=ax,
        edge_color='#888888',
        width=edge_widths,
        alpha=0.6,
        arrows=True,
        arrowsize=20,
        arrowstyle='-|>',
        connectionstyle='arc3,rad=0.1'
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        graph, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors='#333333',
        linewidths=2
    )

    # Draw labels
    labels = {n: graph.nodes[n].get('name', n) for n in graph.nodes}
    nx.draw_networkx_labels(
        graph, pos, labels, ax=ax,
        font_size=9,
        font_weight='bold'
    )

    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=plt.cm.Blues(0.3), edgecolor='#333', label='Few visits'),
        mpatches.Patch(facecolor=plt.cm.Blues(1.0), edgecolor='#333', label='Many visits'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)

    # Add stats text
    stats_text = f"Pages: {len(graph.nodes)} | Paths: {len(graph.edges)}"
    ax.text(0.5, -0.05, stats_text, transform=ax.transAxes,
            ha='center', fontsize=10, color='#666666')

    ax.set_axis_off()
    plt.tight_layout()

    # Save the figure
    graph_image_path = os.path.join(output_dir, "knowledge_graph.png")
    plt.savefig(graph_image_path, dpi=150, bbox_inches='tight', facecolor='white')

    print(f"  {colored('KNOWLEDGE GRAPH IMAGE SAVED TO:', Colors.YELLOW + Colors.BOLD)}")
    print(f"    {colored(graph_image_path, Colors.GREEN)}")

    plt.show()
