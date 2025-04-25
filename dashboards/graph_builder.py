import networkx as nx

def build_graph(world: dict) -> nx.Graph:
    g = nx.Graph()
    # add agents
    for name in world["agents"]:
        g.add_node(name, kind="agent")
    # add objects
    for oid, rec in world["objects"].items():
        g.add_node(oid, kind=rec.get("kind", "object"))
        creator = rec.get("creator")
        if creator:
            g.add_edge(creator, oid, rel="owns")
    # parent lineage
    for child, rec in world["agents"].items():
        for parent in rec.get("parents", []):
            if parent in world["agents"]:
                g.add_edge(parent, child, rel="parent")
    return g 