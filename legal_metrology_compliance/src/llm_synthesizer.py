import os
import json
import re

class LLMLegalSynthesizer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("[LLM ENGINE] Successfully initialized Gemini LLM Client!")
            except Exception as e:
                print(f"[LLM ENGINE NOTICE] Gemini client initialization error: {e}")
        else:
            print("[LLM ENGINE NOTICE] No GEMINI_API_KEY found in environment. Using Hybrid Rule Engine + Heuristic LLM Parser.")

    def synthesize_with_llm(self, doc_info):
        """
        Uses Gemini LLM to semantically analyze a legal PDF document text 
        and extract structured gazette notification metadata and rules.
        """
        if not self.client:
            return None

        prompt = f"""
        You are an expert Legal Metrology AI assistant for the Department of Consumer Affairs (DoCA), India.
        Analyze the following text extracted from a Legal Metrology Gazette PDF:
        
        Document Filename: {doc_info['filename']}
        
        === EXTRACTED LEGAL TEXT ===
        {doc_info['raw_text']}
        ============================
        
        Extract the following legal details in pure valid JSON format:
        1. "notification_no": Gazette Notification number (e.g., G.S.R. 779(E) or N/A)
        2. "date": Date of notification or publication
        3. "effective_date": Date when rules come into force
        4. "is_amendment": true if this document amends/substitutes/inserts previous rules, false if baseline
        5. "amended_clauses": List of objects with keys:
           - "clause": Clause name (e.g., "Rule 6(1)(e)", "Rule 6(1)(ea)")
           - "action": "SUBSTITUTE" | "INSERT" | "OMIT" | "BASELINE"
           - "title": Title of rule
           - "summary": Summary of legal directive
           - "regex_pattern": Standard Python regex string to extract this mandatory field from product labels
        
        Return ONLY valid JSON without markdown formatting.
        """

        # Model candidates to try in order of capability
        model_candidates = ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        
        for model_name in model_candidates:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                data = json.loads(text.strip())
                print(f"[LLM SUCCESS ({model_name})] Extracted legal metadata for {doc_info['filename']}")
                return data
            except Exception as e:
                # Try next model if 404 / unavailable
                continue

        return None
