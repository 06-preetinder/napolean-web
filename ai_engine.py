import re
import numpy as np
from collections import Counter

# Lazy ML placeholders
SentenceTransformer = None
spacy = None
KeyBERT = None


class NapoleanAI:
    _shared_embedder = None
    _shared_nlp = None
    _shared_keyword_model = None
    _ml_loaded = False

    @classmethod
    def _ensure_ml_libs(cls):
        global SentenceTransformer, spacy, KeyBERT
        if not cls._ml_loaded:
            try:
                from sentence_transformers import SentenceTransformer as _ST
                import spacy as _spacy
                from keybert import KeyBERT as _KB
                SentenceTransformer = _ST
                spacy = _spacy
                KeyBERT = _KB
                cls._ml_loaded = True
            except Exception as e:
                print(f"[AI] Error importing heavy ML libraries: {e}")

    def __init__(self, intent_text=None, intent_keywords=None):
        NapoleanAI._ensure_ml_libs()
        
        # Load spaCy (fast & local)
        if NapoleanAI._shared_nlp is None and spacy is not None:
            try:
                NapoleanAI._shared_nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                print(f"[AI Warning] Could not load spacy en_core_web_sm: {e}")
                NapoleanAI._shared_nlp = None

        # Only load SentenceTransformer if an intent is actually specified!
        if intent_text and NapoleanAI._shared_embedder is None and SentenceTransformer is not None:
            print("[AI] Loading semantic embedding model for intent analysis...")
            try:
                NapoleanAI._shared_embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"[AI Warning] SentenceTransformer fallback to keyword matching: {e}")
                NapoleanAI._shared_embedder = None

        if NapoleanAI._shared_keyword_model is None and NapoleanAI._shared_embedder is not None and KeyBERT is not None:
            try:
                NapoleanAI._shared_keyword_model = KeyBERT(NapoleanAI._shared_embedder)
            except Exception:
                NapoleanAI._shared_keyword_model = None

        self.embedder = NapoleanAI._shared_embedder
        self.nlp = NapoleanAI._shared_nlp
        self.keyword_model = NapoleanAI._shared_keyword_model

        self.intent_text = intent_text
        self.intent_embedding = None
        self.intent_keywords = intent_keywords or []
        
        if intent_text:
            if self.embedder:
                try:
                    self.intent_embedding = self.embedder.encode(intent_text, convert_to_numpy=True)
                except Exception:
                    self.intent_embedding = None
            if self.nlp:
                self.intent_keywords = self._extract_intent_keywords(intent_text)
            else:
                self.intent_keywords = [w.lower() for w in intent_text.split() if len(w) > 3]

    def _extract_intent_keywords(self, text):
        """Extract keywords from intent text for multiple matching strategies"""
        if not self.nlp:
            return [w.lower() for w in text.split() if len(w) > 3]
        doc = self.nlp(text)
        keywords = set()
        for chunk in doc.noun_chunks:
            keywords.add(chunk.text.lower())
        for ent in doc.ents:
            keywords.add(ent.text.lower())
        for token in doc:
            if not token.is_stop and not token.is_punct and len(token.text) > 3:
                keywords.add(token.lemma_.lower())
        return list(keywords)

    def extract_keywords(self, text, top_n=5):
        if self.keyword_model:
            try:
                keywords = self.keyword_model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 2),
                    stop_words="english",
                    top_n=top_n
                )
                return [kw[0] for kw in keywords]
            except Exception:
                pass

        # Fast NLP fallback (instant & high accuracy)
        if self.nlp and text:
            try:
                doc = self.nlp(text[:2000])
                words = [t.lemma_.lower() for t in doc if not t.is_stop and not t.is_punct and len(t.text) > 3]
                counts = Counter(words)
                return [w for w, _ in counts.most_common(top_n)]
            except Exception:
                pass
        return []

    def get_page_embedding(self, text):
        return self.embedder.encode(text, convert_to_numpy=True)

    def relevance_score(self, page_text, chunk_size=500):
        """
        Enhanced relevance scoring with multiple signals:
        1. Semantic embedding similarity (chunked)
        2. Keyword matching boost
        3. Entity matching boost
        """
        if self.intent_embedding is None or not page_text:
            return 0.0
        
        # Signal 1: Semantic similarity with chunks
        words = page_text.split()
        if len(words) < 10:
            return 0.0
        
        # Create overlapping chunks for better coverage
        chunks = []
        step = max(1, int(chunk_size / 2))  # 50% overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk) > 50:
                chunks.append(chunk)
        
        if not chunks:
            return 0.0
        
        try:
            # Get embeddings for all chunks
            chunk_embeddings = self.embedder.encode(
                chunks,
                batch_size=16,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            intent_emb = np.array(self.intent_embedding, dtype=np.float32)
            
            # Compute cosine similarities
            norms = np.linalg.norm(chunk_embeddings, axis=1)
            intent_norm = np.linalg.norm(intent_emb)
            
            # Avoid division by zero
            norms = np.where(norms == 0, 1e-8, norms)
            
            sims = np.dot(chunk_embeddings, intent_emb) / (norms * intent_norm)
            best_semantic_score = float(np.max(sims))
            avg_semantic_score = float(np.mean(sims))
            
        except Exception as e:
            print(f"[AI ERROR] Semantic scoring failed: {e}")
            best_semantic_score = 0.0
            avg_semantic_score = 0.0
        
        # Signal 2: Keyword matching
        keyword_score = self._keyword_match_score(page_text)
        
        # Signal 3: Entity matching
        entity_score = self._entity_match_score(page_text)
        
        # Weighted combination: semantic is primary, but keywords and entities boost the score
        # This ensures pages with strong intent signals get higher scores
        final_score = (
            0.5 * best_semantic_score + 
            0.2 * avg_semantic_score + 
            0.15 * keyword_score + 
            0.15 * entity_score
        )
        
        # Boost if any signal is very strong
        if best_semantic_score > 0.5 or keyword_score > 0.5 or entity_score > 0.5:
            final_score = min(1.0, final_score * 1.2)
        
        return round(final_score, 3)
    
    def _keyword_match_score(self, text):
        """Calculate keyword matching score"""
        if not self.intent_keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = 0
        
        for keyword in self.intent_keywords:
            # Use word boundary matching for better accuracy
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower, re.IGNORECASE):
                matches += 1
        
        # Normalize to 0-1 range
        return min(1.0, matches / max(1, len(self.intent_keywords) * 0.3))
    
    def _entity_match_score(self, text):
        """Calculate entity matching score"""
        if not self.intent_keywords:
            return 0.0
        
        try:
            doc = self.nlp(text[:10000])  # Limit text length for performance
            text_entities = set(ent.text.lower() for ent in doc.ents)
            
            matches = 0
            for keyword in self.intent_keywords:
                for entity in text_entities:
                    if keyword in entity or entity in keyword:
                        matches += 1
                        break
            
            return min(1.0, matches / max(1, len(self.intent_keywords) * 0.3))
        except:
            return 0.0
    
    def score_link(self, url: str, anchor_text: str = "", context_text: str = "") -> float:
        """
        Score a link before crawling to determine priority.
        This enables intelligent pre-filtering of links.
        
        Signals:
        1. URL path matching
        2. Anchor text matching
        3. Context text matching
        """
        if not self.intent_text:
            return 0.5  # Default medium priority if no intent
        
        score = 0.0
        signals_found = 0
        
        # Signal 1: URL path matching
        url_lower = url.lower()
        for keyword in self.intent_keywords:
            if keyword in url_lower:
                score += 0.4
                signals_found += 1
                break
        
        # Signal 2: Anchor text matching (strongest indicator)
        if anchor_text:
            anchor_lower = anchor_text.lower()
            for keyword in self.intent_keywords:
                if keyword in anchor_lower:
                    score += 0.5
                    signals_found += 1
                    break
        
        # Signal 3: Context text matching
        if context_text:
            context_lower = context_text.lower()
            for keyword in self.intent_keywords:
                if keyword in context_lower:
                    score += 0.3
                    signals_found += 1
                    break
        
        # Normalize: if we found multiple signals, boost confidence
        if signals_found > 1:
            score = min(1.0, score * 1.2)
        
        # Use semantic similarity if we have enough context
        if anchor_text or context_text:
            combined_text = (anchor_text + " " + context_text).strip()
            if len(combined_text) > 20:
                try:
                    emb = self.embedder.encode(combined_text, convert_to_numpy=True)
                    intent_emb = np.array(self.intent_embedding, dtype=np.float32)
                    norm_emb = np.linalg.norm(emb)
                    norm_intent = np.linalg.norm(intent_emb)
                    if norm_emb > 0 and norm_intent > 0:
                        semantic_sim = np.dot(emb, intent_emb) / (norm_emb * norm_intent)
                        # Blend semantic with keyword matching
                        score = 0.6 * score + 0.4 * float(semantic_sim)
                except:
                    pass
        
        return round(min(1.0, score), 3)

    def extract_entities(self, text):
        doc = self.nlp(text)
        return [
        {"text": ent.text, "type": ent.label_}
        for ent in doc.ents  
        ]
        
    def summarize(self, text, max_len=400):
         sentences = re.split(r'(?<=[.!?]) +', text)
         summary = ""

         for s in sentences:
             if len(summary) + len(s) < max_len:
                summary += s + " "
             else:
                break

         return summary.strip()

    def analyze_page(self, page_data):
        
        text = page_data.get("text", "")
        if not text:
            return None
        relevance = self.relevance_score(text)
        keywords = self.extract_keywords(text)
        entities = self.extract_entities(text)
        entity_counts = Counter(ent["text"] for ent in entities)
        summary = self.summarize(text)
        page_data.update({
            "relevance_score": relevance,
            "entities": entities,
            "keywords": keywords,
            "entity_frequency": dict(entity_counts),
            "summary": summary
        })
        return page_data

