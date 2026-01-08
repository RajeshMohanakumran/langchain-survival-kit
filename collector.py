"""
Data Collector - Extracts documentation and patterns from LangChain GitHub
"""

import os
import json
import re
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

DATA_DIR = Path("data")
RAW_DOCS_DIR = DATA_DIR / "raw_docs"
PATTERNS_FILE = DATA_DIR / "patterns.json"

# GitHub API endpoints
GITHUB_API = "https://api.github.com"
REPO = "langchain-ai/langchain"
DOCS_PATH = "docs/docs"


class DataCollector:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        RAW_DOCS_DIR.mkdir(exist_ok=True)
        self.patterns = []
        
    def collect_from_github(self):
        """Collect documentation files from GitHub"""
        print("📥 Fetching LangChain documentation from GitHub...")
        
        # Get directory tree
        url = f"{GITHUB_API}/repos/{REPO}/contents/{DOCS_PATH}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            items = response.json()
        except Exception as e:
            print(f"❌ Failed to fetch from GitHub: {e}")
            print("💡 Using manual patterns instead...")
            self._create_manual_patterns()
            return
        
        # Download markdown files
        count = 0
        for item in items[:20]:  # Limit to avoid rate limiting
            if item['type'] == 'file' and item['name'].endswith(('.md', '.mdx')):
                self._download_file(item)
                count += 1
        
        print(f"✅ Downloaded {count} documentation files")
        
    def _download_file(self, item):
        """Download a single file from GitHub"""
        try:
            response = requests.get(item['download_url'])
            response.raise_for_status()
            
            file_path = RAW_DOCS_DIR / item['name']
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Extract patterns from this file
            self._extract_patterns(response.text, item['name'])
            
        except Exception as e:
            print(f"⚠️ Failed to download {item['name']}: {e}")
    
    def _extract_patterns(self, content, source):
        """Extract deprecation patterns from documentation"""
        
        # Pattern 1: from X import Y style changes
        imports = re.findall(
            r'from\s+(langchain[\w._]*)\s+import\s+([\w, ]+)',
            content
        )
        
        for module, items in imports:
            # Detect if it's old or new style
            if 'langchain_' in module:
                # New style
                self.patterns.append({
                    "type": "import",
                    "new_style": f"from {module} import {items.strip()}",
                    "module": module,
                    "source": source
                })
            elif '.' in module and 'langchain.' in module:
                # Old style
                self.patterns.append({
                    "type": "import",
                    "old_style": f"from {module} import {items.strip()}",
                    "module": module,
                    "source": source
                })
        
        # Pattern 2: "use X instead of Y"
        replacements = re.findall(
            r'use\s+`([^`]+)`\s+instead\s+of\s+`([^`]+)`',
            content,
            re.IGNORECASE
        )
        
        for new, old in replacements:
            self.patterns.append({
                "type": "replacement",
                "old": old,
                "new": new,
                "source": source
            })
        
        # Pattern 3: deprecated mentions
        deprecated = re.findall(
            r'`([^`]+)`\s+is\s+deprecated',
            content,
            re.IGNORECASE
        )
        
        for item in deprecated:
            self.patterns.append({
                "type": "deprecated",
                "item": item,
                "source": source
            })
    
    def _create_manual_patterns(self):
        """Create comprehensive manual pattern database"""
        self.patterns = [
            # OpenAI imports
            {
                "old": "from langchain.llms import OpenAI",
                "new": "from langchain_openai import OpenAI",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.chat_models import ChatOpenAI",
                "new": "from langchain_openai import ChatOpenAI",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.embeddings import OpenAIEmbeddings",
                "new": "from langchain_openai import OpenAIEmbeddings",
                "type": "import",
                "confidence": "high"
            },
            
            # Chain deprecations
            {
                "old": "from langchain.chains import LLMChain",
                "new": "Use LCEL: prompt | llm",
                "type": "chain_deprecation",
                "confidence": "high",
                "explanation": "LLMChain is deprecated. Use LangChain Expression Language (LCEL) instead."
            },
            {
                "old": "LLMChain(llm=llm, prompt=prompt)",
                "new": "prompt | llm",
                "type": "usage",
                "confidence": "high"
            },
            
            # Document loaders
            {
                "old": "from langchain.document_loaders import TextLoader",
                "new": "from langchain_community.document_loaders import TextLoader",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.document_loaders import PyPDFLoader",
                "new": "from langchain_community.document_loaders import PyPDFLoader",
                "type": "import",
                "confidence": "high"
            },
            
            # Vector stores
            {
                "old": "from langchain.vectorstores import FAISS",
                "new": "from langchain_community.vectorstores import FAISS",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.vectorstores import Chroma",
                "new": "from langchain_community.vectorstores import Chroma",
                "type": "import",
                "confidence": "high"
            },
            
            # Text splitters
            {
                "old": "from langchain.text_splitter import RecursiveCharacterTextSplitter",
                "new": "from langchain_text_splitters import RecursiveCharacterTextSplitter",
                "type": "import",
                "confidence": "high"
            },
            
            # Embeddings
            {
                "old": "from langchain.embeddings import HuggingFaceEmbeddings",
                "new": "from langchain_huggingface import HuggingFaceEmbeddings",
                "type": "import",
                "confidence": "high"
            },
            
            # Prompts
            {
                "old": "from langchain.prompts import PromptTemplate",
                "new": "from langchain_core.prompts import PromptTemplate",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.prompts import ChatPromptTemplate",
                "new": "from langchain_core.prompts import ChatPromptTemplate",
                "type": "import",
                "confidence": "high"
            },
            
            # Schema/Messages
            {
                "old": "from langchain.schema import Document",
                "new": "from langchain_core.documents import Document",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.schema import HumanMessage",
                "new": "from langchain_core.messages import HumanMessage",
                "type": "import",
                "confidence": "high"
            },
            {
                "old": "from langchain.schema import AIMessage",
                "new": "from langchain_core.messages import AIMessage",
                "type": "import",
                "confidence": "high"
            },
            
            # Agents
            {
                "old": "from langchain.agents import initialize_agent",
                "new": "from langchain.agents import create_react_agent",
                "type": "import",
                "confidence": "high",
                "explanation": "initialize_agent is deprecated. Use create_react_agent instead."
            },
            
            # Output parsers
            {
                "old": "from langchain.output_parsers import PydanticOutputParser",
                "new": "from langchain_core.output_parsers import PydanticOutputParser",
                "type": "import",
                "confidence": "high"
            },
            
            # Callbacks
            {
                "old": "from langchain.callbacks import StreamingStdOutCallbackHandler",
                "new": "from langchain_core.callbacks import StreamingStdOutCallbackHandler",
                "type": "import",
                "confidence": "high"
            },
        ]
    
    def save_patterns(self):
        """Save patterns to JSON file"""
        output = {
            "collected_at": datetime.now().isoformat(),
            "total_patterns": len(self.patterns),
            "patterns": self.patterns
        }
        
        with open(PATTERNS_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Saved {len(self.patterns)} patterns to {PATTERNS_FILE}")
    
    def run(self):
        """Main collection pipeline"""
        print("=" * 60)
        print("🚀 LangChain Data Collection")
        print("=" * 60)
        
        # Try GitHub first, fall back to manual
        self.collect_from_github()
        
        # Always add manual patterns
        if not self.patterns:
            self._create_manual_patterns()
        
        self.save_patterns()
        
        print(f"\n✅ Collection complete!")
        print(f"📊 Total patterns: {len(self.patterns)}")


if __name__ == "__main__":
    collector = DataCollector()
    collector.run()