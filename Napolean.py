import requests
import selenium
from bs4 import BeautifulSoup
import argparse
import queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from urllib.parse import urljoin,urlunparse, parse_qsl, urlencode, urlparse
import random
from data_extractor import extract_page_content
from storage_manager import StorageManager
from ai_engine import NapoleanAI
from security_scanner import SecurityScanner, run_security_scan
from report_generator import ResearchReportGenerator, generate_research_report
from graph_builder import GraphBuilder
HEADERS = {"User-Agent": "subfinder-combined/1.0 (+https://example.com)"}
DEFAULT_TIMEOUT = 5


def get_selenium_driver(headless=False, window_size=(1200, 800)):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    return driver


def fetch_html_with_requests(url , timeout=DEFAULT_TIMEOUT ):
    try:
        response= requests.get(url=url , headers=HEADERS , timeout=timeout , allow_redirects=True)
        return response.status_code, response.text
    except Exception as e:
        print(f"[Error fetching {url}]: {e}")
        return None,None
    

def fetch_html_with_selenium(url , driver , wait=2):
    try:
        driver.get(url)
        WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.page_source
    except Exception as e:
        print(f"[Error fetching {url}]: {e}")
        return None


def validate_link(url, base_domain):
    if not url.startswith(("https://", "http://")):
        return False
    # Compare actual hosts, not substrings — "base_domain not in url" let a
    # URL like https://evil.com/?to=https://example.com slip through before,
    # since the target domain just had to appear anywhere in the string.
    try:
        url_host = urlparse(url).netloc.lower()
        base_host = urlparse(base_domain).netloc.lower()
    except Exception:
        return False
    if url_host != base_host:
        return False
    if url.endswith((".jpg", ".json", ".png", ".exe", ".pdf", ".zip")):
        return False
    return True

def normalize_link(url: str) -> str:
    try:
        # Add default scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)

        # Only keep valid domains
        if not parsed.netloc:
            return None

        # Normalize domain (lowercase)
        netloc = parsed.netloc.lower()

        # Remove query params and fragments for clean comparison
        cleaned = parsed._replace(
            scheme=parsed.scheme,
            netloc=netloc,
            path=parsed.path.rstrip('/'),
            params="",
            query="",
            fragment=""
        )

        # Rebuild URL
        normalized_url = urlunparse(cleaned)
        return normalized_url

    except Exception as e:
        print(f"[Error normalizing {url}]: {e}")
        return None

def extract_links_from_html(html , base_domain):
    soup=BeautifulSoup(html or "" , "html.parser")
    links=set()
    
    for a in soup.find_all("a" , href=True):
        href=a["href"].strip()
        full=urljoin(base_domain , href)
        if validate_link(url=full , base_domain=base_domain):
            links.add(normalize_link(full))
    return links

def napoleon_banner():
    banner = r""" 
███╗   ██╗ █████╗ ██████╗  ██████╗ ██╗     ███████╗ ██████╗ ███╗   ██╗
████╗  ██║██╔══██╗██╔══██╗██╔═══██╗██║     ██╔════╝██╔═══██╗████╗  ██║
██╔██╗ ██║███████║██████╔╝██║   ██║██║     █████╗  ██║   ██║██╔██╗ ██║
██║╚██╗██║██╔══██║██╔═══╝ ██║   ██║██║     ██╔══╝  ██║   ██║██║╚██╗██║
██║ ╚████║██║  ██║██║     ╚██████╔╝███████╗███████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
      """
    print("\033[1;33m" + banner + "\033[0m")  # gold color
    print("⚜️  NAPOLEON CRAWLER v1.0 — 'The Empire Expands Digitally'")
    print("------------------------------------------------------------")
    print("Author     : Emperor Napoléon Bonaparte (and Preetinderjeet Singh)")
    print("Operation  : Web Reconnaissance and Link Expansion")
    print("Motto      : 'Conquer, Index, and Rule the Internet!'")
    print("------------------------------------------------------------\n")
    print("📣  'Soldiers of code! Today, we embark on a campaign not of blood,")
    print("     but of bandwidth. The web shall remember our crawl!'")
    print("------------------------------------------------------------\n")


def get_base_domain(url):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def crawl(start_url, max_depth=10, use_selenium=False , storage=None , ai=None):
    napoleon_banner()
    q = queue.Queue()
    visited = set()
    queued = set()

    driver = get_selenium_driver() if use_selenium else None
    print(f"🗡️ 'We march upon {start_url} — destiny favors the bold!'")
    print(f"⚙️ Strategy: Depth={max_depth}, Method={'Selenium' if use_selenium else 'Requests'}\n")
    q.put((start_url, 0))
    queued.add(start_url)

    base_domain = get_base_domain(start_url)

    while not q.empty():
        url, depth = q.get()
        queued.discard(url)

        if url in visited or depth > max_depth:
            continue
        print(f"\n🎖️ 'Forward! We advance to depth {depth} — {url}'")
        
        visited.add(url)
        status, html = fetch_html_with_requests(url=url)
        
        if not isinstance(html, str) or not html.strip():
            if use_selenium:
                
                html = fetch_html_with_selenium(url, driver)
                
        if not isinstance(html, str) or not html.strip():
            print(f"⚠️ 'The fortress {url} stands defiant — our scouts report failure.'")
            continue
        
        # Extract links first (needed for both crawling and storage)
        links = extract_links_from_html(html=html, base_domain=base_domain)
        
        # 🧠 Extract and store page content
        if storage:
            try:
                page_data = extract_page_content(html, url)
                if page_data:
                    # Add extracted links to page data for graph generation
                    page_data["links"] = list(links) if links else []
                    
                    # ensure ai exists before using
                    if ai:
                        enriched = ai.analyze_page(page_data)
                    else:
                        enriched = page_data

                    if not enriched:
                        continue

                    score = enriched.get("relevance_score", 0.0)

                    if ai and ai.intent_text and score < 0.25:
                        print(f"⚙️ [Filtered] Low relevance ({score}) — skipping {url}")
                        continue

                    # store cleaned numeric score back (optional but helpful)
                    enriched["relevance_score"] = float(score)

                    storage.add_record(enriched)
                    print(f"🧠 [Analyzed] {url} | Relevance={enriched['relevance_score']}")
            except Exception as e:
                print(f"[AI Analysis Error] Failed to analyze {url}: {e}")
                continue

        
        print(f"📜 'We discovered {len(links)} new passages through {url}.'")

        victory_quotes = [
            "🗺️ 'The map expands — glory to our conquest!'",
            "⚔️ 'Every link conquered is another step toward dominion.'",
            "📯 'Our banners now fly higher, soldier!'",
            "🔥 'Let none stand unvisited — march onward!'",
            "🏰 'Victory favors those who persist.'"
        ]
        if links:
            print(random.choice(victory_quotes))

        for link in links:
            if link not in visited and link not in queued:
                q.put((link, depth + 1))
                queued.add(link)
    if storage:
        storage.save()
        storage.close()

    if driver:
        driver.quit()

    print(f"\n🏁 'Campaign complete — {len(visited)} territories brought under our flag.'")
    print("💀 'History shall remember this crawl as one of precision and might.'")
    print("⚙️ Mission complete. Vive l’Empereur!")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Napolean - AI-based Intelligent Web Crawler")
    parser.add_argument("--intent", type=str, help="Specify crawl intent (e.g. 'cybersecurity research')")
    parser.add_argument("--url", required=True, help="Starting URL to crawl (e.g. https://example.com)")
    parser.add_argument("--depth", type=int, default=10, help="Maximum crawl depth (default: 10)")
    parser.add_argument("--method", choices=["requests", "selenium"], default="requests",
                        help="Crawling method to use (default: requests)")
    parser.add_argument("--headless", action="store_true",
                        help="Run Selenium in headless mode (no browser window)")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds (default: 5)")
    parser.add_argument("--napoleon-mode", action="store_true",
                        help="Enable Napoleon-style conversational output")
    parser.add_argument("--save-json", default="output/crawled.json",
                        help="Path to JSON file for storing extracted data (default: output/crawled.json)")
    parser.add_argument("--save-sqlite", default=None,
                        help="Optional SQLite database path to store structured crawl data (e.g. output/crawled.db)")
    parser.add_argument("--no-save", action="store_true",
                        help="Disable saving any crawled data to disk")
    
    # Security scanning options
    parser.add_argument("--scan-security", action="store_true",
                        help="Run security scan on crawled data after crawling")
    parser.add_argument("--security-report", default="output/security_report.json",
                        help="Path to save security report (default: output/security_report.json)")
    
    # Report generation options
    parser.add_argument("--generate-report", action="store_true",
                        help="Generate research report from crawled data")
    parser.add_argument("--report-output", default="output/research_report.json",
                        help="Path to save research report (default: output/research_report.json)")
    parser.add_argument("--data-file", default="output/crawled.json",
                        help="Path to crawled data JSON file for report generation (default: output/crawled.json)")
    
    # Graph generation options
    parser.add_argument("--generate-graph", action="store_true",
                        help="Generate network graph from crawled data")
    parser.add_argument("--graph-output", default="output/network_graph.html",
                        help="Path to save network graph (default: output/network_graph.html)")
    parser.add_argument("--entity-graph-output", default="output/entity_graph.html",
                        help="Path to save entity graph (default: output/entity_graph.html)")

    return parser.parse_args()


def main():
    args = parse_arguments()
    ai = NapoleanAI(intent_text=args.intent)

    start_url = normalize_link(args.url)
    use_selenium = args.method == "selenium"
    # 🧱 Storage setup
    if args.no_save:
        storage = None
    else:
        storage = StorageManager(
        json_path=args.save_json,
        sqlite_path=args.save_sqlite
    )


    if args.napoleon_mode:
        print("⚔️  Napolean: Troops, prepare for conquest! The domain awaits!")
        print(f"🎯  Target: {start_url} | Max Depth: {args.depth} | Method: {args.method}")
    else:
        print(f"Starting crawl on {start_url} (depth={args.depth}, method={args.method})")

    try:
        crawl(
            start_url=start_url,
            max_depth=args.depth,
            use_selenium=use_selenium,
            storage=storage,
            ai=ai
            )

        # Run security scan if requested
        if args.scan_security:
            print("\n[Security] Running security scan on crawled data...")
            import json
            try:
                with open(args.save_json, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                
                scanner = SecurityScanner()
                for page in crawled_data:
                    url = page.get("url", "")
                    html = page.get("text", "")
                    if html:
                        scanner.scan_page(url, html)
                
                scanner.print_report()
                scanner.save_report(args.security_report)
                print(f"[Security] Security report saved to {args.security_report}")
            except Exception as e:
                print(f"[Security] Error running security scan: {e}")

        # Generate research report if requested
        if args.generate_report:
            print("\n[Report] Generating research report...")
            try:
                generator = ResearchReportGenerator(data_file=args.data_file)
                generator.generate_report()
                generator.save_report(args.report_output)
                generator.print_report()
                print(f"[Report] Research report saved to {args.report_output}")
            except Exception as e:
                print(f"[Report] Error generating report: {e}")

        # Generate network graph if requested
        if args.generate_graph:
            print("\n[Graph] Generating network graph from crawled data...")
            try:
                import json
                with open(args.save_json, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                
                graph_builder = GraphBuilder()
                
                # Build crawl graph from URLs and links
                for page in crawled_data:
                    url = page.get("url", "")
                    if not url:
                        continue
                    
                    # Get outgoing links from the page
                    links = page.get("links", [])
                    for link in links:
                        graph_builder.add_page_link(url, link)
                
                # Build entity graph from entities
                for page in crawled_data:
                    url = page.get("url", "")
                    entities = page.get("entities", [])
                    if url and entities:
                        graph_builder.add_entities(url, entities)
                
                # Save graphs
                graph_builder.save_crawl_graph(args.graph_output)
                graph_builder.save_entity_graph(args.entity_graph_output)
                
                print(f"[Graph] Network graph saved to {args.graph_output}")
                print(f"[Graph] Entity graph saved to {args.entity_graph_output}")
            except Exception as e:
                print(f"[Graph] Error generating graph: {e}")

        if args.napoleon_mode:
            print("🏆  Napolean: Victory! The empire has been mapped successfully.")
        else:
            print("Crawl completed successfully.")

    except KeyboardInterrupt:
        if args.napoleon_mode:
            print("\n💀  Napolean: Retreat! The campaign has been aborted by user command.")
        else:
            print("\nCrawl aborted by user.")
    except Exception as e:
        if args.napoleon_mode:
            print(f"💣  Napolean: Disaster struck! Error — {e}")
        else:
            print(f"Error: {e}")
    finally:
        print("⚙️  Mission complete.")


if __name__ == "__main__":
    main()





    
    
