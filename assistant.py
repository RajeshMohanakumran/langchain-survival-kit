"""
Core Assistant Logic - Syntax detection and AI-powered suggestions
"""

import os
import json
import re
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

PATTERNS_FILE = Path("data/patterns.json")
VECTOR_DB_PATH = "vectorstore"


class SyntaxAssistant:
    def __init__(self, groq_api_key=None):
        """Initialize the syntax assistant"""
        
        # Load embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Load vector store
        self.vector_store = None
        if os.path.exists(VECTOR_DB_PATH):
            self.vector_store = FAISS.load_local(
                VECTOR_DB_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        
        # Load patterns
        self.patterns = []
        if PATTERNS_FILE.exists():
            with open(PATTERNS_FILE, 'r') as f:
                data = json.load(f)
                self.patterns = data.get('patterns', [])
        
        # Initialize LLM
        self.llm = None
        if groq_api_key:
            self.llm = ChatGroq(
                api_key=groq_api_key,
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
    
    def extract_imports(self, code):
        """Extract import statements from code"""
        imports = []
        
        # Pattern for from X import Y
        from_imports = re.finditer(
            r'from\s+([\w.]+)\s+import\s+([\w, ]+)',
            code
        )
        
        for match in from_imports:
            imports.append({
                "type": "from_import",
                "module": match.group(1),
                "items": match.group(2),
                "full": match.group(0),
                "line": code[:match.start()].count('\n') + 1
            })
        
        # Pattern for import X
        direct_imports = re.finditer(r'import\s+([\w.]+)', code)
        
        for match in direct_imports:
            imports.append({
                "type": "import",
                "module": match.group(1),
                "full": match.group(0),
                "line": code[:match.start()].count('\n') + 1
            })
        
        return imports
    
    def detect_issues(self, code):
        """Detect deprecated syntax in code"""
        imports = self.extract_imports(code)
        issues = []
        
        # Check each import against patterns
        for imp in imports:
            for pattern in self.patterns:
                old_syntax = pattern.get('old', pattern.get('old_style', ''))
                
                if imp['full'] in old_syntax or imp['module'] in old_syntax:
                    issues.append({
                        "line": imp['line'],
                        "found": imp['full'],
                        "suggestion": pattern.get('new', pattern.get('new_style', 'Check documentation')),
                        "type": pattern.get('type', 'unknown'),
                        "confidence": pattern.get('confidence', 'medium'),
                        "explanation": pattern.get('explanation', '')
                    })
                    break
        
        # Check for specific usage patterns (like LLMChain)
        if 'LLMChain(' in code:
            issues.append({
                "line": code.find('LLMChain('),
                "found": "LLMChain usage",
                "suggestion": "Use LCEL: prompt | llm",
                "type": "usage_deprecation",
                "confidence": "high",
                "explanation": "LLMChain is deprecated. Use LangChain Expression Language instead."
            })
        
        return issues
    
    def get_rag_context(self, query, k=3):
        """Get relevant context from RAG"""
        if not self.vector_store:
            return ""
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return "\n\n".join([d.page_content for d in docs])
        except:
            return ""
    
    def analyze_with_ai(self, code, issues):
        """Get AI-powered explanation and suggestions"""
        if not self.llm:
            return None
        
        # Get RAG context
        query = " ".join([i['found'] for i in issues])
        context = self.get_rag_context(query)
        
        prompt = f"""You are a LangChain migration expert. Analyze this code and provide migration guidance.

Code issues found:
{json.dumps(issues, indent=2)}

Documentation context:
{context}

Provide:
1. Brief explanation of what changed
2. Updated code with correct imports
3. Key migration tips

Be concise and practical. Focus on actionable advice."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"AI analysis failed: {str(e)}"
    
    def analyze_code(self, code, use_ai=True):
        """Complete code analysis"""
        issues = self.detect_issues(code)
        
        result = {
            "issues": issues,
            "issues_count": len(issues),
            "ai_explanation": None
        }
        
        if issues and use_ai and self.llm:
            result["ai_explanation"] = self.analyze_with_ai(code, issues)
        
        return result