import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", re.I)

def visible_text(soup):
    #extract text from p , section and other tages 
    parts=[]
    for el in soup.find_all(["p","section","article"]):
        text= el.get_text(separator=' ' , strip = True)
        if text:
            parts.append(text)
    return "\n\n".join(parts)
       
def extract_page_content(html, url):
    if not html:
        return {}
    
    soup=BeautifulSoup(html , "html.parser")
    
    if soup.title and soup.title.string:  #getting the title string 
        title = soup.title.string.strip()
    else:
        return None
    
    meta_desc = ""
    m = soup.find("meta", attrs={"name": "description"})
    if m and m.get("content"):
        meta_desc = m["content"].strip()
    
    headings = []
    for tag in ["h1","h2","h3"]:
        for h in soup.find_all(tag):
            t=h.get_text(strip=True)
            if t :
               headings.append(t)
    
    text = visible_text(soup)
    
    scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    
    emails = list(set(EMAIL_RE.findall(html)))
    
    forms= []
    for f in soup.find_all("form"):
         forms.append({
            "action": f.get("action"),
            "method": f.get("method", "get").lower(),
            "inputs": [inp.get("name") for inp in f.find_all("input") if inp.get("name")]
        })

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "text": text,
        "emails": emails,
        "scripts": scripts,
        "forms": forms
    }
