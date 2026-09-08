"""
Security Scanner Module for NapoleanAI
Provides vulnerability detection and reconnaissance capabilities
"""

import re
import json
import os
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from bs4 import BeautifulSoup


# Common vulnerability patterns
SQLI_PATTERNS = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    r"(\w*)\s*=\s*(\w*)\s*OR\s*(\w*)\s*=\s*(\w*)",
    r"UNION\s+ALL\s+SELECT",
    r"EXEC\s*\(",
    r"(\d+)\s*=\s*(\d+)",
]

XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"eval\s*\(",
]

SENSITIVE_FILES = [
    ".env", ".git/config", ".svn/entries",
    "wp-config.php", "config.php", "settings.py",
    ".DS_Store", "Thumbs.db",
    "phpinfo.php", "info.php",
    ".htaccess", ".htpasswd",
    "id_rsa", "id_dsa", "id_ecdsa",
    "credentials.json", "secrets.json",
]

ADMIN_PATTERNS = [
    r"/admin", r"/administrator", r"/manage",
    r"/cms", r"/wp-admin", r"/dashboard",
    r"/login", r"/signin", r"/auth",
    r"/backend", r"/panel", r"/control",
]

SENSITIVE_DATA_PATTERNS = [
    (r"(api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "API Key"),
    (r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Password"),
    (r"(secret|token|auth)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Secret Token"),
    (r"aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*['\"][A-Z0-9]{20}['\"]", "AWS Key"),
    (r"sk-[a-zA-Z0-9]{48,}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Token"),
    (r"xox[baprs]-[a-zA-Z0-9]{10,}", "Slack Token"),
    (r"AIza[0-9A-Za-z\\-_]{35}", "Google API Key"),
    (r"rk_live_[0-9a-zA-Z]{24,}", "Stripe Restricted Key"),
    (r"sk_live_[0-9a-zA-Z]{24,}", "Stripe Secret Key"),
    (r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----", "Private Key Block"),
    (r"mongodb(?:\+srv)?:\/\/[^\s\"']+", "MongoDB Connection String"),
    (r"postgres(?:ql)?:\/\/[^\s\"']+", "PostgreSQL Connection String"),
]

TECHNOLOGY_SIGNATURES = {
    "WordPress": ["wp-content", "wp-includes", "wp-admin"],
    "Drupal": ["drupal", "sites/default"],
    "Joomla": ["joomla", "option=com"],
    "React": ["react", "react-dom"],
    "Vue": ["vue.js", "vuejs"],
    "Angular": ["angular", "@angular"],
    "jQuery": ["jquery", "jQuery"],
    "Bootstrap": ["bootstrap", "bootstrap.css"],
    "Node.js": ["node_modules", "express"],
    "Django": ["django", "csrftoken"],
    "Laravel": ["laravel", "X-CSRF-TOKEN"],
    "PHP": [".php", "PHPSESSID"],
    "ASP.NET": ["__VIEWSTATE", "asp.net"],
    "Apache": ["Apache"],
    "Nginx": ["nginx"],
}


class SecurityScanner:
    """Security vulnerability scanner and reconnaissance tool"""
    
    def __init__(self):
        self.findings = []
        self.technology_stack = set()
        
    def scan_page(self, url, html, headers=None):
        """Scan a single page for security issues"""
        findings = []
        
        # Technology detection
        tech = self.detect_technology(html, headers or {})
        if tech:
            self.technology_stack.update(tech)
            findings.append({
                "type": "technology",
                "severity": "info",
                "title": "Technology Stack Detected",
                "description": f"Technologies found: {', '.join(tech)}",
                "url": url
            })
        
        # Check for sensitive files in links
        sensitive = self.check_sensitive_files(url, html)
        findings.extend(sensitive)
        
        # Check for SQL injection vectors
        sqli = self.check_sqli_vectors(url, html)
        findings.extend(sqli)
        
        # Check for XSS vectors
        xss = self.check_xss_vectors(url, html)
        findings.extend(xss)
        
        # Check for admin panels
        admin = self.check_admin_panels(url, html)
        findings.extend(admin)
        
        # Check for sensitive data exposure
        sensitive_data = self.check_sensitive_data(url, html)
        findings.extend(sensitive_data)
        
        # Check for email addresses (OSINT)
        emails = self.extract_emails(url, html)
        if emails:
            findings.append({
                "type": "osint",
                "severity": "info",
                "title": "Email Addresses Found",
                "description": f"Found {len(emails)} email(s): {', '.join(emails[:5])}",
                "url": url,
                "emails": emails
            })
        
        # Check for API endpoints
        api_endpoints = self.detect_api_endpoints(url, html)
        if api_endpoints:
            findings.append({
                "type": "reconnaissance",
                "severity": "info",
                "title": "API Endpoints Discovered",
                "description": f"Found {len(api_endpoints)} API endpoint(s)",
                "url": url,
                "endpoints": api_endpoints
            })
        
        # Check forms for security issues
        form_issues = self.analyze_forms(url, html)
        findings.extend(form_issues)
        
        # Check for interesting URL parameters
        param_issues = self.analyze_url_params(url)
        findings.extend(param_issues)
        
        self.findings.extend(findings)
        return findings
    
    def detect_technology(self, html, headers):
        """Detect technologies used by the website"""
        technologies = []
        
        # Check headers
        server = headers.get("Server", "")
        x_powered = headers.get("X-Powered-By", "")
        
        for tech, signatures in TECHNOLOGY_SIGNATURES.items():
            for sig in signatures:
                if sig.lower() in (server + x_powered + html).lower():
                    technologies.append(tech)
        
        # Check HTML meta tags
        soup = BeautifulSoup(html, "html.parser")
        
        # Generator meta
        generator = soup.find("meta", attrs={"name": "generator"})
        if generator and generator.get("content"):
            technologies.append(generator["content"])
        
        # Check for specific scripts
        scripts = soup.find_all("script", src=True)
        for script in scripts:
            src = script["src"].lower()
            if "jquery" in src:
                technologies.append("jQuery")
            if "react" in src:
                technologies.append("React")
            if "vue" in src:
                technologies.append("Vue.js")
            if "angular" in src:
                technologies.append("Angular")
        
        return list(set(technologies))
    
    def check_sensitive_files(self, url, html):
        """Check if links point to potentially sensitive files"""
        findings = []
        soup = BeautifulSoup(html, "html.parser")
        
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            for sensitive in SENSITIVE_FILES:
                if sensitive in href:
                    findings.append({
                        "type": "sensitive_file",
                        "severity": "medium",
                        "title": "Sensitive File Reference",
                        "description": f"Link to potential sensitive file: {href}",
                        "url": url,
                        "evidence": href
                    })
        
        return findings
    
    def check_sqli_vectors(self, url, html):
        """Check for potential SQL injection vectors"""
        findings = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Check forms with query parameters
        for form in soup.find_all("form"):
            action = form.get("action", "")
            method = form.get("method", "get").lower()
            
            # Check if form submits to URL with parameters
            if "?" in action or method == "get":
                # Check for SQL injection patterns in input names
                for inp in form.find_all(["input", "textarea"]):
                    name = inp.get("name", "").lower()
                    if any(pattern in name for pattern in ["id", "user", "search", "query", "id", "cat"]):
                        findings.append({
                            "type": "sqli_vector",
                            "severity": "low",
                            "title": "Potential SQL Injection Vector",
                            "description": f"Form input '{name}' may be vulnerable to SQL injection",
                            "url": url,
                            "form_action": action
                        })
        
        return findings
    
    def check_xss_vectors(self, url, html):
        """Check for potential XSS vectors"""
        findings = []
        soup = BeautifulSoup(html, "html.parser")
        
        for form in soup.find_all("form"):
            for inp in form.find_all("input"):
                inp_type = inp.get("type", "text").lower()
                if inp_type in ["text", "search"]:
                    name = inp.get("name", "").lower()
                    # Check if there's no obvious sanitization
                    parent = inp.find_parent("form")
                    if parent:
                        findings.append({
                            "type": "xss_vector",
                            "severity": "low",
                            "title": "Potential XSS Vector",
                            "description": f"Input '{name}' could be vulnerable to XSS if not properly sanitized",
                            "url": url
                        })
        
        return findings
    
    def check_admin_panels(self, url, html):
        """Check for admin panel links"""
        findings = []
        soup = BeautifulSoup(html, "html.parser")
        
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            for admin_pattern in ADMIN_PATTERNS:
                if admin_pattern in href:
                    findings.append({
                        "type": "admin_panel",
                        "severity": "info",
                        "title": "Admin Panel Detected",
                        "description": f"Potential admin panel found: {href}",
                        "url": url,
                        "evidence": href
                    })
        
        return findings
    
    def check_sensitive_data(self, url, html):
        """Check for exposed sensitive data"""
        findings = []
        
        for pattern, description in SENSITIVE_DATA_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                findings.append({
                    "type": "sensitive_data",
                    "severity": "critical",
                    "title": f"Exposed {description}",
                    "description": f"Potential {description} found in HTML",
                    "url": url,
                    "count": len(matches)
                })
        
        return findings
    
    def extract_emails(self, url, html):
        """Extract email addresses for OSINT"""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, html)
        return list(set(emails))
    
    def detect_api_endpoints(self, url, html):
        """Detect potential API endpoints"""
        endpoints = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Check script tags for API calls
        for script in soup.find_all("script"):
            src = script.get("src", "")
            if "api" in src.lower():
                endpoints.append(src)
            
            # Check for fetch/axios calls in inline scripts
            if script.string:
                if "fetch(" in script.string or "axios" in script.string:
                    # Extract URL patterns
                    urls = re.findall(r'["\'](/?api[^\'"]+)["\']', script.string)
                    endpoints.extend(urls)
        
        return list(set(endpoints))
    
    def analyze_forms(self, url, html):
        """Analyze forms for security issues"""
        findings = []
        soup = BeautifulSoup(html, "html.parser")
        
        for form in soup.find_all("form"):
            action = form.get("action", "")
            method = form.get("method", "get").lower()
            
            # Check for GET method on sensitive forms
            if method == "get" and ("login" in action or "password" in action):
                findings.append({
                    "type": "form_security",
                    "severity": "medium",
                    "title": "Insecure Form Method",
                    "description": f"Form uses GET method which exposes data in URL",
                    "url": url,
                    "form_action": action
                })
            
            # Check for missing CSRF token (common patterns)
            has_csrf = form.find("input", attrs={"name": re.compile(r"csrf|token|_token)", re.I)})
            if not has_csrf:
                findings.append({
                    "type": "form_security",
                    "severity": "low",
                    "title": "Potential Missing CSRF Token",
                    "description": "Form may be missing CSRF protection",
                    "url": url,
                    "form_action": action
                })
            
            # Check for password fields without autocomplete off
            password_fields = form.find_all("input", {"type": "password"})
            for pf in password_fields:
                autocomplete = pf.get("autocomplete", "")
                if autocomplete != "off":
                    findings.append({
                        "type": "form_security",
                        "severity": "low",
                        "title": "Password Autocomplete Enabled",
                        "description": "Password field should have autocomplete='off'",
                        "url": url
                    })
        
        return findings
    
    def analyze_url_params(self, url):
        """Analyze URL parameters for security issues"""
        findings = []
        parsed = urlparse(url)
        params = parsed.query
        
        if not params:
            return findings
        
        # Check for sensitive parameter names
        sensitive_params = ["token", "key", "secret", "password", "auth", "id", "admin"]
        param_dict = {}
        
        for param in params.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                param_dict[key.lower()] = value
        
        for sp in sensitive_params:
            if sp in param_dict:
                findings.append({
                    "type": "url_parameter",
                    "severity": "medium",
                    "title": "Sensitive Parameter in URL",
                    "description": f"Parameter '{sp}' found in URL query string (exposed in logs)",
                    "url": url,
                    "parameter": sp
                })
        
        return findings
    
    def get_summary(self):
        """Get summary of all findings"""
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for finding in self.findings:
            severity_counts[finding["severity"]] += 1
            type_counts[finding["type"]] += 1
        
        return {
            "total_findings": len(self.findings),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "technologies": list(self.technology_stack)
        }
    
    def get_critical_findings(self):
        """Get only critical/high severity findings"""
        return [f for f in self.findings if f["severity"] in ["critical", "high"]]
    
    def save_report(self, output_file="output/security_report.json"):
        """Save security report to file"""
        report = {
            "summary": self.get_summary(),
            "findings": self.findings,
            "critical_findings": self.get_critical_findings()
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[Security] Report saved to {output_file}")
        return report
    
    def print_report(self):
        """Print security findings to console"""
        print("\n" + "=" * 70)
        print("              SECURITY SCAN REPORT")
        print("=" * 70)
        
        summary = self.get_summary()
        print(f"\n[TOTAL FINDINGS: {summary['total_findings']}]")
        
        if summary["technologies"]:
            print(f"\n[TECHNOLOGIES DETECTED]")
            for tech in summary["technologies"]:
                print(f"  - {tech}")
        
        print(f"\n[BY SEVERITY]")
        for sev, count in summary["by_severity"].items():
            icon = "🔴" if sev == "critical" else "🟠" if sev == "high" else "🟡" if sev == "medium" else "🔵"
            print(f"  {icon} {sev.upper()}: {count}")
        
        print(f"\n[BY TYPE]")
        for ftype, count in summary["by_type"].items():
            print(f"  - {ftype}: {count}")
        
        # Show critical findings
        critical = self.get_critical_findings()
        if critical:
            print(f"\n[CRITICAL FINDINGS]")
            for i, finding in enumerate(critical, 1):
                print(f"  {i}. {finding['title']}")
                print(f"     URL: {finding['url']}")
                print(f"     {finding['description']}")
        
        print("\n" + "=" * 70)
        
        return summary


def run_security_scan(url, html, headers=None):
    """Convenience function to run security scan"""
    scanner = SecurityScanner()
    findings = scanner.scan_page(url, html, headers)
    
    print(f"\n[Security] Scanned {url}: {len(findings)} findings")
    
    return scanner

