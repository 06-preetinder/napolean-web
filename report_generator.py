import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any


class ResearchReportGenerator:
    """
    Generates comprehensive research reports from crawled data.
    """
    
    def __init__(self, data_file: str = "output/crawled.json"):
        self.data_file = data_file
        self.data = []
        self.report = {}
        
    def load_data(self) -> bool:
        """Load crawled data from JSON file"""
        if not os.path.exists(self.data_file):
            print(f"[Report] Data file not found: {self.data_file}")
            return False
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return len(self.data) > 0
        except Exception as e:
            print(f"[Report] Failed to load data: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive research report"""
        if not self.data:
            if not self.load_data():
                return {"error": "No data available to generate report"}
        
        report = {
            "metadata": self._generate_metadata(),
            "summary": self._generate_summary(),
            "important_entities": self._extract_important_entities(),
            "key_insights": self._generate_key_insights(),
            "top_pages": self._get_top_pages(),
            "entity_analysis": self._analyze_entities(),
            "topic_analysis": self._analyze_topics(),
            "url_analysis": self._analyze_urls()
        }
        
        self.report = report
        return report
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            "report_type": "AI Crawl Research Report",
            "generated_at": datetime.now().isoformat(),
            "data_source": self.data_file,
            "total_pages": len(self.data)
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall summary"""
        if not self.data:
            return {"error": "No data available"}
        
        # Calculate statistics
        total_pages = len(self.data)
        avg_relevance = sum(p.get("relevance_score", 0) for p in self.data) / total_pages if total_pages > 0 else 0
        
        # Count entities
        all_entities = []
        for page in self.data:
            entities = page.get("entities", [])
            all_entities.extend([e["text"] for e in entities])
        
        entity_count = len(all_entities)
        unique_entities = len(set(all_entities))
        
        # Count keywords
        all_keywords = []
        for page in self.data:
            keywords = page.get("keywords", [])
            all_keywords.extend(keywords)
        
        # Pages with content
        pages_with_text = sum(1 for p in self.data if p.get("text"))
        
        return {
            "total_pages_crawled": total_pages,
            "pages_with_content": pages_with_text,
            "average_relevance_score": round(avg_relevance, 3),
            "total_entities_found": entity_count,
            "unique_entities": unique_entities,
            "total_keywords": len(all_keywords),
            "high_relevance_pages": sum(1 for p in self.data if p.get("relevance_score", 0) > 0.7),
            "medium_relevance_pages": sum(1 for p in self.data if 0.4 < p.get("relevance_score", 0) <= 0.7),
            "low_relevance_pages": sum(1 for p in self.data if p.get("relevance_score", 0) <= 0.4)
        }
    
    def _extract_important_entities(self) -> List[Dict[str, Any]]:
        """Extract most important entities across all pages"""
        entity_frequency = Counter()
        entity_pages = defaultdict(set)
        
        for page in self.data:
            url = page.get("url", "")
            entities = page.get("entities", [])
            for entity in entities:
                text = entity.get("text", "")
                entity_type = entity.get("type", "UNKNOWN")
                entity_frequency[(text, entity_type)] += 1
                entity_pages[(text, entity_type)].add(url)
        
        # Get top entities by frequency
        important_entities = []
        for (text, entity_type), count in entity_frequency.most_common(30):
            # Calculate importance score based on frequency and relevance of pages it's in
            pages = entity_pages[(text, entity_type)]
            page_scores = [p.get("relevance_score", 0) for p in self.data if p.get("url") in pages]
            avg_page_score = sum(page_scores) / len(page_scores) if page_scores else 0
            
            important_entities.append({
                "entity": text,
                "type": entity_type,
                "frequency": count,
                "appears_in_pages": len(pages),
                "avg_page_relevance": round(avg_page_score, 3),
                "importance_score": round((count * 0.6 + avg_page_score * len(pages) * 0.4) / 2, 3)
            })
        
        return important_entities[:20]  # Top 20
    
    def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        if not self.data:
            return ["No data available for analysis"]
        
        # Insight 1: Relevance distribution
        high_rel = sum(1 for p in self.data if p.get("relevance_score", 0) > 0.7)
        med_rel = sum(1 for p in self.data if 0.4 < p.get("relevance_score", 0) <= 0.7)
        low_rel = sum(1 for p in self.data if p.get("relevance_score", 0) <= 0.4)
        
        if high_rel > len(self.data) * 0.3:
            insights.append(f"High relevance: {high_rel} pages ({high_rel*100//len(self.data)}%) scored above 0.7, indicating strong alignment with research intent.")
        
        # Insight 2: Entity concentration
        all_entities = []
        for page in self.data:
            all_entities.extend([e["text"] for e in page.get("entities", [])])
        
        if all_entities:
            most_common = Counter(all_entities).most_common(5)
            entities_str = ", ".join([f"'{e[0]}'" for e in most_common])
            insights.append(f"Most frequently mentioned entities: {entities_str}")
        
        # Insight 3: Topic coverage
        all_keywords = []
        for page in self.data:
            all_keywords.extend(page.get("keywords", []))
        
        if all_keywords:
            top_keywords = Counter(all_keywords).most_common(5)
            keywords_str = ", ".join([f"'{k[0]}'" for k in top_keywords])
            insights.append(f"Primary topics identified: {keywords_str}")
        
        # Insight 4: Page quality
        pages_with_summary = sum(1 for p in self.data if p.get("summary"))
        if pages_with_summary > len(self.data) * 0.8:
            insights.append(f"Content quality is high: {pages_with_summary} out of {len(self.data)} pages have extractable summaries.")
        
        # Insight 5: Entity types
        entity_types = Counter()
        for page in self.data:
            for entity in page.get("entities", []):
                entity_types[entity.get("type", "UNKNOWN")] += 1
        
        if entity_types:
            top_types = entity_types.most_common(3)
            types_str = ", ".join([f"{t[0]}({t[1]})" for t in top_types])
            insights.append(f"Entity type distribution: {types_str}")
        
        return insights
    
    def _get_top_pages(self) -> List[Dict[str, Any]]:
        """Get top pages by relevance score"""
        sorted_pages = sorted(
            self.data, 
            key=lambda x: x.get("relevance_score", 0), 
            reverse=True
        )
        
        top_pages = []
        for page in sorted_pages[:10]:
            top_pages.append({
                "url": page.get("url", ""),
                "title": page.get("title", "N/A"),
                "relevance_score": page.get("relevance_score", 0),
                "entities_count": len(page.get("entities", [])),
                "keywords": page.get("keywords", [])[:5],
                "summary": page.get("summary", "")[:200] + "..." if len(page.get("summary", "")) > 200 else page.get("summary", "")
            })
        
        return top_pages
    
    def _analyze_entities(self) -> Dict[str, Any]:
        """Detailed entity analysis"""
        entity_by_type = defaultdict(list)
        
        for page in self.data:
            for entity in page.get("entities", []):
                entity_by_type[entity.get("type", "UNKNOWN")].append(entity.get("text", ""))
        
        analysis = {}
        for entity_type, entities in entity_by_type.items():
            counter = Counter(entities)
            analysis[entity_type] = {
                "count": len(entities),
                "unique": len(set(entities)),
                "top_mentions": dict(counter.most_common(10))
            }
        
        return analysis
    
    def _analyze_topics(self) -> Dict[str, Any]:
        """Analyze topics/keywords across pages"""
        all_keywords = []
        keyword_scores = defaultdict(list)
        
        for page in self.data:
            keywords = page.get("keywords", [])
            score = page.get("relevance_score", 0)
            for kw in keywords:
                all_keywords.append(kw)
                keyword_scores[kw].append(score)
        
        keyword_counter = Counter(all_keywords)
        
        # Calculate avg score per keyword
        keyword_avg_scores = {}
        for kw, scores in keyword_scores.items():
            keyword_avg_scores[kw] = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_keywords": len(all_keywords),
            "unique_keywords": len(set(all_keywords)),
            "top_keywords": dict(keyword_counter.most_common(20)),
            "highest_scoring_keywords": sorted(
                keyword_avg_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
    
    def _analyze_urls(self) -> Dict[str, Any]:
        """Analyze URL patterns"""
        domains = defaultdict(int)
        
        for page in self.data:
            url = page.get("url", "")
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
                domains[domain] += 1
        
        return {
            "domains_crawled": dict(domains),
            "total_domains": len(domains)
        }
    
    def save_report(self, output_file: str = "output/research_report.json"):
        """Save report to JSON file"""
        if not self.report:
            self.generate_report()
        
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else "output", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"[Report] Research report saved to {output_file}")
        return output_file
    
    def print_report(self):
        """Print report in readable format"""
        if not self.report:
            self.generate_report()
        
        r = self.report
        
        print("\n" + "=" * 70)
        print("                    RESEARCH REPORT")
        print("=" * 70)
        
        # Metadata
        if "metadata" in r:
            print("\n[METADATA]")
            for k, v in r["metadata"].items():
                print(f"  {k}: {v}")
        
        # Summary
        if "summary" in r:
            print("\n[SUMMARY]")
            for k, v in r["summary"].items():
                print(f"  {k}: {v}")
        
        # Important Entities
        if "important_entities" in r:
            print("\n[TOP ENTITIES]")
            for i, ent in enumerate(r["important_entities"][:10], 1):
                print(f"  {i}. {ent['entity']} ({ent['type']})")
                print(f"     Frequency: {ent['frequency']} | Importance: {ent['importance_score']}")
        
        # Key Insights
        if "key_insights" in r:
            print("\n[KEY INSIGHTS]")
            for i, insight in enumerate(r["key_insights"], 1):
                print(f"  {i}. {insight}")
        
        # Top Pages
        if "top_pages" in r:
            print("\n[TOP RELEVANT PAGES]")
            for i, page in enumerate(r["top_pages"][:5], 1):
                print(f"  {i}. {page['title']}")
                print(f"     URL: {page['url']}")
                print(f"     Score: {page['relevance_score']}")
        
        print("\n" + "=" * 70)
        
        return r


def generate_research_report(data_file: str = "output/crawled.json", output_file: str = None):
    """Convenience function to generate and save report"""
    generator = ResearchReportGenerator(data_file)
    report = generator.generate_report()
    
    if output_file is None:
        output_file = "output/research_report.json"
    
    generator.save_report(output_file)
    generator.print_report()
    
    return report

