"""
Graph Builder Module for Napoléon
Produces lightweight, high-performance graph representations for both
web visualization and standalone HTML generation.
"""

import json
import os
import networkx as nx
from urllib.parse import urlparse

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False


class GraphBuilder:
    def __init__(self):
        self.crawl_graph = nx.DiGraph()
        self.entity_graph = nx.Graph()
        self.node_metadata = {}

    def add_page(self, url, title=None, relevance=0.0):
        """Ensure page is registered as a node even if it has no links."""
        if not url:
            return
        self.crawl_graph.add_node(url)
        if url not in self.node_metadata:
            self.node_metadata[url] = {
                "label": self._short_label(url),
                "title": title or url,
                "url": url,
                "type": "page",
                "relevance": relevance,
            }

    def add_page_link(self, source, target, source_title=None, relevance=0.0):
        """Add directed link between source page and target page."""
        if not source or not target:
            return
        self.crawl_graph.add_edge(source, target)
        if source not in self.node_metadata:
            self.node_metadata[source] = {
                "label": self._short_label(source),
                "title": source_title or source,
                "url": source,
                "type": "page",
                "relevance": relevance,
            }
        if target not in self.node_metadata:
            self.node_metadata[target] = {
                "label": self._short_label(target),
                "title": target,
                "url": target,
                "type": "page",
                "relevance": 0.0,
            }

    def add_entities(self, page_url, entities, page_title=None):
        """Add entities linked to a page."""
        if not page_url or not entities:
            return
        
        if page_url not in self.node_metadata:
            self.node_metadata[page_url] = {
                "label": self._short_label(page_url),
                "title": page_title or page_url,
                "url": page_url,
                "type": "page",
                "relevance": 0.0,
            }
        
        for ent in entities:
            name = ent.get("text", "") if isinstance(ent, dict) else str(ent)
            label = ent.get("label", "ENTITY") if isinstance(ent, dict) else "ENTITY"
            if not name or len(name) < 2:
                continue

            ent_id = f"entity:{name.lower()}"
            self.entity_graph.add_node(ent_id)
            self.entity_graph.add_edge(page_url, ent_id)

            if ent_id not in self.node_metadata:
                self.node_metadata[ent_id] = {
                    "label": name,
                    "title": f"{label}: {name}",
                    "entity_type": label,
                    "type": "entity",
                }

    def _short_label(self, url):
        """Extract a readable short path or domain for visual compactness."""
        try:
            parsed = urlparse(url)
            path = parsed.path.rstrip('/')
            if not path or path == "":
                return parsed.netloc or url
            parts = path.split('/')
            return parts[-1] if parts[-1] else parsed.netloc
        except Exception:
            return url[:30]

    def to_lightweight_dict(self, mode="crawl"):
        """
        Export graph as lightweight JSON data for hardware-accelerated frontend rendering.
        mode: 'crawl', 'entity', or 'unified'
        """
        if mode == "crawl":
            g = self.crawl_graph
        elif mode == "entity":
            g = self.entity_graph
        else:
            g = nx.compose(self.crawl_graph.to_undirected(), self.entity_graph)

        nodes = []
        edges = []

        if g.number_of_nodes() == 0:
            return {"nodes": [], "edges": [], "stats": {"nodes": 0, "edges": 0}}

        degrees = dict(g.degree())
        max_deg = max(degrees.values()) if degrees else 1

        for n in g.nodes():
            meta = self.node_metadata.get(n, {})
            node_type = meta.get("type", "page")
            deg = degrees.get(n, 1)
            size = 12 + int((deg / max(1, max_deg)) * 25)

            if node_type == "entity":
                color = "#c5a059"  # Imperial Gold
            elif meta.get("relevance", 0) > 0.6:
                color = "#27ae60"  # High relevance green
            else:
                color = "#2c3e50"  # Deep imperial navy

            nodes.append({
                "id": str(n),
                "label": meta.get("label", str(n)[:25]),
                "title": meta.get("title", str(n)),
                "type": node_type,
                "entity_type": meta.get("entity_type", ""),
                "url": meta.get("url", ""),
                "relevance": meta.get("relevance", 0.0),
                "value": deg,
                "size": size,
                "color": color,
            })

        for u, v in g.edges():
            edges.append({
                "from": str(u),
                "to": str(v),
                "color": {"color": "rgba(180, 160, 120, 0.4)", "highlight": "#d4af37"},
                "width": 1.2,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "nodes": len(nodes),
                "edges": len(edges),
                "graph_type": mode,
            }
        }

    def save_json(self, path="output/graph_data.json", mode="crawl"):
        """Save lightweight JSON representation."""
        data = self.to_lightweight_dict(mode=mode)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[GraphBuilder] Lightweight graph JSON saved to {path}")
        return data

    def save_crawl_graph(self, path="output/crawl_graph.html"):
        """Save HTML crawl graph with fast stabilization options."""
        if self.crawl_graph.number_of_nodes() == 0:
            print("[GraphBuilder] No nodes in crawl graph to save.")
            return

        json_path = path.replace(".html", ".json")
        self.save_json(json_path, mode="crawl")

        if not PYVIS_AVAILABLE:
            return

        try:
            net = Network(height="700px", width="100%", directed=True, bgcolor="#0f172a", font_color="#e2e8f0")
            for node in self.crawl_graph.nodes():
                meta = self.node_metadata.get(node, {})
                label = meta.get("label", str(node)[:25])
                net.add_node(node, label=label, title=node, color="#c5a059", size=15)

            for u, v in self.crawl_graph.edges():
                net.add_edge(u, v, color="rgba(197, 160, 89, 0.35)")

            net.set_options("""
            {
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -2000,
                  "centralGravity": 0.2,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09
                },
                "maxVelocity": 50,
                "minVelocity": 0.75,
                "stabilization": {
                  "enabled": true,
                  "iterations": 50,
                  "updateInterval": 25
                }
              },
              "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": true
              }
            }
            """)
            net.save_graph(path)
            print(f"[GraphBuilder] Optimized crawl graph HTML saved to {path}")
        except Exception as e:
            print(f"[GraphBuilder] Error generating PyVis HTML: {e}")

    def save_entity_graph(self, path="output/entity_graph.html"):
        """Save entity graph HTML with fast stabilization."""
        if self.entity_graph.number_of_nodes() == 0:
            print("[GraphBuilder] No nodes in entity graph to save.")
            return

        json_path = path.replace(".html", ".json")
        self.save_json(json_path, mode="entity")

        if not PYVIS_AVAILABLE:
            return

        try:
            net = Network(height="700px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0")
            for node in self.entity_graph.nodes():
                meta = self.node_metadata.get(node, {})
                is_entity = meta.get("type") == "entity"
                color = "#dfb76c" if is_entity else "#3b82f6"
                label = meta.get("label", str(node)[:25])
                net.add_node(node, label=label, title=meta.get("title", node), color=color, size=18 if is_entity else 12)

            for u, v in self.entity_graph.edges():
                net.add_edge(u, v, color="rgba(223, 183, 108, 0.35)")

            net.set_options("""
            {
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -2500,
                  "centralGravity": 0.25,
                  "springLength": 85,
                  "springConstant": 0.05,
                  "damping": 0.09
                },
                "stabilization": {
                  "enabled": true,
                  "iterations": 50
                }
              },
              "interaction": {
                "hover": true,
                "navigationButtons": true
              }
            }
            """)
            net.save_graph(path)
            print(f"[GraphBuilder] Optimized entity graph HTML saved to {path}")
        except Exception as e:
            print(f"[GraphBuilder] Error generating PyVis entity graph: {e}")

