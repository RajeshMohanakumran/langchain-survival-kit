"""
RAG Ingestion Pipeline - Creates vector database from collected data
"""

import os
import json
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

RAW_DOCS_DIR = Path("data/raw_docs")
PATTERNS_FILE = Path("data/patterns.json")
VECTOR_DB_PATH = "vectorstore"


class RAGIngestor:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.documents = []
    
    def load_markdown_docs(self):
        """Load markdown documentation files"""
        if not RAW_DOCS_DIR.exists():
            print("⚠️ No raw docs found, skipping...")
            return
        
        print("📄 Loading markdown files...")
        
        md_files = list(RAW_DOCS_DIR.glob("*.md")) + list(RAW_DOCS_DIR.glob("*.mdx"))
        
        for file_path in md_files:
            try:
                loader = TextLoader(str(file_path), encoding="utf-8")
                docs = loader.load()
                self.documents.extend(docs)
            except Exception as e:
                print(f"⚠️ Failed to load {file_path.name}: {e}")
        
        print(f"✅ Loaded {len(self.documents)} documents")
    
    def load_patterns(self):
        """Load and convert patterns to documents"""
        if not PATTERNS_FILE.exists():
            print("⚠️ No patterns file found")
            return
        
        print("📊 Loading patterns...")
        
        with open(PATTERNS_FILE, 'r') as f:
            data = json.load(f)
        
        patterns = data.get('patterns', [])
        
        for pattern in patterns:
            # Create searchable document from pattern
            content = f"""
Syntax Pattern:
Old: {pattern.get('old', pattern.get('old_style', 'N/A'))}
New: {pattern.get('new', pattern.get('new_style', 'N/A'))}
Type: {pattern.get('type', 'unknown')}
{f"Explanation: {pattern.get('explanation', '')}" if pattern.get('explanation') else ""}
"""
            
            doc = Document(
                page_content=content,
                metadata={
                    "type": "pattern",
                    "pattern_type": pattern.get('type', 'unknown'),
                    "source": pattern.get('source', 'manual')
                }
            )
            self.documents.append(doc)
        
        print(f"✅ Loaded {len(patterns)} patterns")
    
    def create_vector_store(self):
        """Create FAISS vector store"""
        if not self.documents:
            print("❌ No documents to ingest!")
            return
        
        print("✂️ Splitting documents...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n## ", "\n### ", "\n\n", "\n", " "]
        )
        
        chunks = text_splitter.split_documents(self.documents)
        print(f"✅ Created {len(chunks)} chunks")
        
        print("🔄 Creating vector embeddings...")
        
        vector_store = FAISS.from_documents(chunks, self.embeddings)
        vector_store.save_local(VECTOR_DB_PATH)
        
        print(f"✅ Vector store saved to {VECTOR_DB_PATH}")
    
    def run(self):
        """Main ingestion pipeline"""
        print("=" * 60)
        print("🚀 RAG Ingestion Pipeline")
        print("=" * 60)
        
        self.load_markdown_docs()
        self.load_patterns()
        self.create_vector_store()
        
        print("\n✅ Ingestion complete!")
        print(f"📊 Total documents indexed: {len(self.documents)}")


if __name__ == "__main__":
    ingestor = RAGIngestor()
    ingestor.run()