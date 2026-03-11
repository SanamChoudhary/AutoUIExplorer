"""
Comprehension scoring based on navigation patterns.

** NOTE: This is a very basic heuristic model for demonstration purposes.
"""


def calculate_comprehension(pages_visited: int, total_navigations: int, unique_paths: int) -> dict:
    """Calculate comprehension level based on navigation statistics.

    Args:
        pages_visited: Number of distinct pages the user visited.
        total_navigations: Total navigation events recorded.
        unique_paths: Number of unique directed edges in the knowledge graph.

    Returns:
        A dict with keys: level, description, pages_visited,
        total_navigations, unique_paths.
    """
    if pages_visited >= 10 and unique_paths >= 8:
        level = "Expert"
        description = "Thorough exploration with deep navigation"
    elif pages_visited >= 6 and unique_paths >= 4:
        level = "Proficient"
        description = "Good coverage of key areas"
    elif pages_visited >= 3:
        level = "Exploring"
        description = "Basic familiarity with the site"
    elif pages_visited >= 1:
        level = "Novice"
        description = "Just getting started"
    else:
        level = "None"
        description = "No pages visited"

    return {
        "level": level,
        "description": description,
        "pages_visited": pages_visited,
        "total_navigations": total_navigations,
        "unique_paths": unique_paths
    }
