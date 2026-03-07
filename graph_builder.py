import networkx as nx
from pyvis.network import Network


class GraphBuilder:

    def __init__(self):
        self.crawl_graph = nx.DiGraph()
        self.entity_graph = nx.Graph()

    # -----------------------
    # Crawl Graph
    # -----------------------

    def add_page_link(self, source, target):
        self.crawl_graph.add_edge(source, target)

    def save_crawl_graph(self, path="output/crawl_graph.html"):
        # Check if graph has nodes before saving
        if self.crawl_graph.number_of_nodes() == 0:
            print("[GraphBuilder] No nodes in crawl graph to save.")
            return
        
        net = Network(height="750px", width="100%", directed=True)
        net.from_nx(self.crawl_graph)
        # Use save_graph for more reliable saving
        net.save_graph(path)
        print(f"[GraphBuilder] Crawl graph saved to {path}")

    # -----------------------
    # Entity Graph
    # -----------------------

    def add_entities(self, page_url, entities):

        for ent in entities:
            name = ent["text"]

            self.entity_graph.add_node(name)

            self.entity_graph.add_edge(page_url, name)

    def save_entity_graph(self, path="output/entity_graph.html"):
        # Check if graph has nodes before saving
        if self.entity_graph.number_of_nodes() == 0:
            print("[GraphBuilder] No nodes in entity graph to save.")
            return

        net = Network(height="750px", width="100%")

        net.from_nx(self.entity_graph)

        # Use save_graph for more reliable saving
        net.save_graph(path)
        print(f"[GraphBuilder] Entity graph saved to {path}")

