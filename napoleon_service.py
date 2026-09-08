"""
Napoléon Service Orchestrator
Runs web crawling campaigns asynchronously with real-time SSE streaming,
telemetry, security scanning, report generation, and graph construction.
"""

import os
import sys
import time
import json
import queue
import random
import threading
from urllib.parse import urlparse
from datetime import datetime

# Local modules
from data_extractor import extract_page_content
from storage_manager import StorageManager
from ai_engine import NapoleanAI
from security_scanner import SecurityScanner
from report_generator import ResearchReportGenerator
from graph_builder import GraphBuilder

# Re-use helpers from Napolean.py
from Napolean import (
    fetch_html_with_requests,
    fetch_html_with_selenium,
    extract_links_from_html,
    normalize_link,
    get_base_domain,
    get_selenium_driver,
    DEFAULT_TIMEOUT
)

NAPOLEON_VICTORY_QUOTES = [
    "The map expands — glory to our conquest!",
    "Every link conquered is another step toward imperial dominion.",
    "Our banners fly higher upon the digital frontier!",
    "Let none stand unvisited — march onward!",
    "Victory favors those who calculate with precision.",
    "A leader is a dealer in hope — and comprehensive intelligence!",
    "Impossible is a word to be found only in the dictionary of fools."
]

class NapoleonService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None
        self.stop_event = threading.Event()
        self.subscribers = []
        self.sub_lock = threading.Lock()
        
        self.state = {
            "status": "idle",  # idle, running, completed, aborted, error
            "target_url": "",
            "intent": "",
            "depth": 1,
            "max_depth": 2,
            "pages_crawled": 0,
            "links_discovered": 0,
            "entities_found": 0,
            "threats_detected": 0,
            "start_time": None,
            "end_time": None,
            "speed": 0.0,
            "recent_logs": [],
            "last_error": None
        }
        self.history_file = os.path.join("output", "campaigns_history.json")
        os.makedirs("output", exist_ok=True)

    def subscribe(self):
        """Register a new SSE client queue."""
        q = queue.Queue(maxsize=1000)
        with self.sub_lock:
            self.subscribers.append(q)
        return q

    def unsubscribe(self, q):
        """Remove an SSE client queue."""
        with self.sub_lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def broadcast(self, event_type, data):
        """Send an SSE event to all connected web clients."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        with self.sub_lock:
            dead_queues = []
            for q in self.subscribers:
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    dead_queues.append(q)
            for q in dead_queues:
                self.subscribers.remove(q)

    def log(self, text, level="info"):
        """Record log message and broadcast to live terminal."""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "text": text
        }
        with self.lock:
            self.state["recent_logs"].append(entry)
            if len(self.state["recent_logs"]) > 500:
                self.state["recent_logs"].pop(0)
        
        self.broadcast("log", entry)
        print(f"[{entry['time']}][{level.upper()}] {text}")

    def get_status(self):
        with self.lock:
            return dict(self.state)

    def stop_campaign(self):
        """Signal running campaign to abort."""
        if self.state["status"] == "running":
            self.stop_event.set()
            self.log("Retreat ordered! Campaign abortion in progress...", "warning")
            return {"status": "stopping"}
        return {"status": "not_running"}

    def start_campaign(self, options):
        """Start a new campaign in a background worker thread."""
        with self.lock:
            if self.state["status"] == "running":
                return {"error": "A campaign is already in progress!"}

            self.stop_event.clear()
            self.state.update({
                "status": "running",
                "target_url": options.get("url", ""),
                "intent": options.get("intent", ""),
                "depth": 0,
                "max_depth": int(options.get("depth", 2)),
                "pages_crawled": 0,
                "links_discovered": 0,
                "entities_found": 0,
                "threats_detected": 0,
                "start_time": time.time(),
                "end_time": None,
                "speed": 0.0,
                "recent_logs": [],
                "last_error": None
            })

        self.thread = threading.Thread(target=self._run_campaign_thread, args=(options,), daemon=True)
        self.thread.start()
        return {"status": "started", "target": options.get("url")}

    def _run_campaign_thread(self, options):
        start_url = options.get("url", "").strip()
        max_depth = int(options.get("depth", 2))
        method = options.get("method", "requests")
        intent = options.get("intent", "").strip()
        scan_sec = options.get("scan_security", True)
        gen_rep = options.get("generate_report", True)
        gen_grp = options.get("generate_graph", True)
        timeout = int(options.get("timeout", DEFAULT_TIMEOUT))

        normalized_start = normalize_link(start_url)
        if not normalized_start:
            self.log(f"Invalid target coordinates: {start_url}", "error")
            with self.lock:
                self.state["status"] = "error"
                self.state["last_error"] = "Invalid URL"
            return

        self.log(f"Imperial Campaign Initiated against: {normalized_start}", "gold")
        self.log(f"Strategy: Max Depth={max_depth} | Reconnaissance Unit={method.upper()} | Intent='{intent or 'General Recon'}'", "info")

        # Initialize modules
        try:
            self.log("Arming intelligence engines and data stores...", "info")
            storage = StorageManager(json_path="output/crawled.json")
            # Clear old buffer for new crawl
            storage.buffer = []

            ai = NapoleanAI(intent_text=intent if intent else None) if intent else NapoleanAI()
            scanner = SecurityScanner() if scan_sec else None
            graph_builder = GraphBuilder() if gen_grp else None
        except Exception as e:
            self.log(f"Engine initialization error: {e}", "error")
            with self.lock:
                self.state["status"] = "error"
                self.state["last_error"] = str(e)
            return

        driver = None
        if method == "selenium":
            try:
                self.log("Deploying Heavy Artillery (Selenium Chrome Driver)...", "info")
                driver = get_selenium_driver(headless=True)
            except Exception as e:
                self.log(f"Selenium deployment failed: {e}. Falling back to Requests.", "warning")
                method = "requests"

        q = queue.Queue()
        visited = set()
        queued = set()

        q.put((normalized_start, 0))
        queued.add(normalized_start)
        base_domain = get_base_domain(normalized_start)

        start_ts = time.time()

        try:
            while not q.empty() and not self.stop_event.is_set():
                url, depth = q.get()
                queued.discard(url)

                if url in visited or depth > max_depth:
                    continue

                visited.add(url)
                with self.lock:
                    self.state["depth"] = depth
                    self.state["pages_crawled"] = len(visited)
                    elapsed = max(0.1, time.time() - start_ts)
                    self.state["speed"] = round(len(visited) / elapsed, 2)

                self.broadcast("progress", {
                    "pages_crawled": self.state["pages_crawled"],
                    "depth": depth,
                    "max_depth": max_depth,
                    "speed": self.state["speed"],
                    "current_url": url
                })

                self.log(f"Advancing to depth {depth} -> {url}", "info")

                # Fetch page
                html = None
                if method == "selenium" and driver:
                    html = fetch_html_with_selenium(url, driver)
                else:
                    status, html = fetch_html_with_requests(url=url, timeout=timeout)

                if not isinstance(html, str) or not html.strip():
                    self.log(f"Fortress {url} was unreachable or silent.", "warning")
                    continue

                # Extract links
                links = extract_links_from_html(html=html, base_domain=base_domain)
                with self.lock:
                    self.state["links_discovered"] += len(links)

                self.log(f"Discovered {len(links)} passages in {url}", "info")

                # Extract page content
                try:
                    page_data = extract_page_content(html, url)
                    if page_data:
                        page_data["links"] = list(links) if links else []
                        
                        # AI enrichment
                        if ai:
                            enriched = ai.analyze_page(page_data)
                        else:
                            enriched = page_data

                        if enriched:
                            rel_score = float(enriched.get("relevance_score", 0.0))
                            if intent and rel_score < 0.2:
                                self.log(f"Territory {url} scored low relevance ({rel_score:.2f}) — skipped.", "warning")
                            else:
                                storage.add_record(enriched)
                                ent_count = len(enriched.get("entities", []))
                                with self.lock:
                                    self.state["entities_found"] += ent_count

                                self.log(f"Territory conquered: '{page_data.get('title', url)}' (Relevance: {rel_score:.2f})", "success")

                                # Graph update
                                if graph_builder:
                                    graph_builder.add_page(url, title=page_data.get("title"), relevance=rel_score)
                                    for link in links:
                                        graph_builder.add_page_link(url, link, source_title=page_data.get("title"), relevance=rel_score)
                                    if enriched.get("entities"):
                                        graph_builder.add_entities(url, enriched.get("entities"), page_title=page_data.get("title"))

                        # Security scan
                        if scanner:
                            sec_findings = scanner.scan_page(url, html)
                            if sec_findings:
                                with self.lock:
                                    self.state["threats_detected"] = len(scanner.findings)
                                for f in sec_findings:
                                    if f.get("severity") in ["critical", "high"]:
                                        self.log(f"THREAT DETECTED: [{f.get('title')}] at {url}", "danger")
                except Exception as ex:
                    self.log(f"Reconnaissance extraction error at {url}: {ex}", "warning")

                # Quote
                if links and random.random() < 0.3:
                    self.log(random.choice(NAPOLEON_VICTORY_QUOTES), "gold")

                # Enqueue new links
                for link in links:
                    if link not in visited and link not in queued:
                        q.put((link, depth + 1))
                        queued.add(link)

                # Responsive throttle
                time.sleep(0.05)

        except Exception as e:
            self.log(f"Campaign encountered unexpected crisis: {e}", "error")
            with self.lock:
                self.state["last_error"] = str(e)

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        # Save results
        self.log("Consolidating imperial records and intelligence dossiers...", "info")
        try:
            storage.save()
            storage.close()
        except Exception as e:
            self.log(f"Storage commit error: {e}", "warning")

        # Security report
        if scanner:
            try:
                scanner.save_report("output/security_report.json")
                self.log(f"Security reconnaissance finalized: {len(scanner.findings)} findings logged.", "info")
            except Exception as e:
                self.log(f"Security report save error: {e}", "warning")

        # Research report
        if gen_rep:
            try:
                rep_gen = ResearchReportGenerator(data_file="output/crawled.json")
                rep_gen.generate_report()
                rep_gen.save_report("output/research_report.json")
                self.log("Imperial Research Dossier successfully compiled.", "success")
            except Exception as e:
                self.log(f"Research dossier generation error: {e}", "warning")

        # Graph export
        if graph_builder:
            try:
                graph_builder.save_json("output/graph_data.json", mode="unified")
                graph_builder.save_crawl_graph("output/network_graph.html")
                graph_builder.save_entity_graph("output/entity_graph.html")
                self.log("Strategic Cartography maps rendered and optimized.", "success")
            except Exception as e:
                self.log(f"Graph generation error: {e}", "warning")

        final_status = "aborted" if self.stop_event.is_set() else "completed"
        with self.lock:
            self.state["status"] = final_status
            self.state["end_time"] = time.time()

        if final_status == "completed":
            self.log(f"VICTORY! Campaign completed: {len(visited)} territories brought under imperial dominion!", "gold")
            self.log("Mission complete. Vive l'Empereur!", "gold")
        else:
            self.log("Campaign halted by imperial decree.", "warning")

        # Save to history
        self._record_history(options, final_status)
        self.broadcast("complete", self.get_status())

    def _record_history(self, options, final_status):
        """Append campaign to history log."""
        try:
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)

            entry = {
                "id": f"campaign_{int(time.time())}",
                "target_url": options.get("url"),
                "intent": options.get("intent"),
                "status": final_status,
                "pages_crawled": self.state["pages_crawled"],
                "links_discovered": self.state["links_discovered"],
                "entities_found": self.state["entities_found"],
                "threats_detected": self.state["threats_detected"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "duration": round(time.time() - (self.state["start_time"] or time.time()), 1)
            }
            history.insert(0, entry)
            history = history[:50]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[NapoleonService] Error saving history: {e}")

    def get_campaign_data(self):
        """Load all intelligence outputs for the frontend dashboard."""
        crawled = []
        security = {"summary": {"total_findings": 0, "by_severity": {}, "technologies": []}, "findings": []}
        report = {}
        graph = {"nodes": [], "edges": [], "stats": {"nodes": 0, "edges": 0}}

        if os.path.exists("output/crawled.json"):
            try:
                with open("output/crawled.json", "r", encoding="utf-8") as f:
                    crawled = json.load(f)
            except Exception:
                pass

        if os.path.exists("output/security_report.json"):
            try:
                with open("output/security_report.json", "r", encoding="utf-8") as f:
                    security = json.load(f)
            except Exception:
                pass

        if os.path.exists("output/research_report.json"):
            try:
                with open("output/research_report.json", "r", encoding="utf-8") as f:
                    report = json.load(f)
            except Exception:
                pass

        if os.path.exists("output/graph_data.json"):
            try:
                with open("output/graph_data.json", "r", encoding="utf-8") as f:
                    graph = json.load(f)
            except Exception:
                pass

        return {
            "crawled": crawled,
            "security": security,
            "report": report,
            "graph": graph,
            "status": self.get_status()
        }

    def get_archives(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
