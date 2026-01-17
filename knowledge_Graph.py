import networkx as nx

knowledgeGraph = nx.DiGraph()

def addNode(url, clickablesCount, graph: nx.DiGraph = knowledgeGraph):
    nodeID = len(graph.nodes) + 1
    graph.add_node(nodeID, url=url, clickablesCount=clickablesCount)
    return nodeID

def addEdge(sourceNodeID, targetNodeID, label=None, graph: nx.DiGraph = knowledgeGraph):
    graph.add_edge(sourceNodeID, targetNodeID, label=label or "click")