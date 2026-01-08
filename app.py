"""
Streamlit App - LangChain Syntax Assistant
"""

import streamlit as st
import os
from pathlib import Path
from assistant import SyntaxAssistant
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="LangChain Syntax Assistant",
    page_icon="🔧",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .issue-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .info-card {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assistant' not in st.session_state:
    st.session_state.assistant = None
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False


def init_assistant():
    """Initialize the assistant"""
    groq_key = st.session_state.get('groq_key') or os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        st.warning("⚠️ No Groq API key provided. AI features will be limited.")
    
    try:
        st.session_state.assistant = SyntaxAssistant(groq_api_key=groq_key)
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize assistant: {e}")
        return False


def main():
    # Header
    st.markdown('<h1 class="main-header">🔧 LangChain Syntax Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Detect and fix deprecated LangChain syntax automatically</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            value=os.getenv('GROQ_API_KEY', ''),
            help="Get your API key from https://console.groq.com"
        )
        st.session_state.groq_key = groq_key
        
        # Initialize button
        if st.button("🚀 Initialize Assistant", type="primary"):
            with st.spinner("Loading models..."):
                if init_assistant():
                    st.success("✅ Assistant initialized!")
        
        st.divider()
        
        # Stats
        st.header("📊 Statistics")
        if st.session_state.assistant:
            st.metric("Patterns Loaded", len(st.session_state.assistant.patterns))
            st.metric("Vector Store", "✅ Loaded" if st.session_state.assistant.vector_store else "❌ Not loaded")
            st.metric("AI Features", "✅ Enabled" if st.session_state.assistant.llm else "⚠️ Limited")
        
        st.divider()
        
        # About
        st.header("ℹ️ About")
        st.markdown("""
        This tool helps you:
        - 🔍 Detect deprecated syntax
        - ✅ Get migration suggestions
        - 🤖 AI-powered explanations
        - 📚 RAG-based context
        
        Built with LangChain, FAISS, and Groq.
        """)
    
    # Main content
    if not st.session_state.assistant:
        st.info("👈 Click 'Initialize Assistant' in the sidebar to get started!")
        
        # Show example
        st.subheader("📝 Example Usage")
        st.code("""
# Old deprecated syntax
from langchain.llms import OpenAI
from langchain.chains import LLMChain

llm = OpenAI()
chain = LLMChain(llm=llm, prompt=prompt)
        """, language="python")
        
        st.markdown("**After analysis, you'll get:**")
        st.markdown("- ❌ Deprecated imports detected")
        st.markdown("- ✅ Modern replacements suggested")
        st.markdown("- 🤖 AI explanation of changes")
        
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Analyze Code", "📚 Pattern Database", "🎓 Learn"])
    
    with tab1:
        st.subheader("Paste your LangChain code below")
        
        # Code input
        code_input = st.text_area(
            "Python Code",
            height=300,
            placeholder="""# Paste your code here, for example:
from langchain.llms import OpenAI
from langchain.chains import LLMChain

llm = OpenAI()
chain = LLMChain(llm=llm, prompt=prompt)
""",
            key="code_input"
        )
        
        col1, col2 = st.columns([1, 5])
        
        with col1:
            use_ai = st.checkbox("Use AI", value=True, help="Get AI-powered explanations")
        
        with col2:
            analyze_btn = st.button("🔍 Analyze Code", type="primary", use_container_width=True)
        
        # Analysis
        if analyze_btn and code_input.strip():
            with st.spinner("Analyzing code..."):
                result = st.session_state.assistant.analyze_code(code_input, use_ai=use_ai)
                st.session_state.analyzed = True
                st.session_state.result = result
        
        # Display results
        if st.session_state.analyzed and 'result' in st.session_state:
            result = st.session_state.result
            
            st.divider()
            
            if result['issues_count'] == 0:
                st.markdown('<div class="success-card">✅ <b>No deprecated syntax detected!</b> Your code looks good.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="issue-card">⚠️ <b>Found {result["issues_count"]} issue(s)</b></div>', unsafe_allow_html=True)
                
                # Show issues
                for i, issue in enumerate(result['issues'], 1):
                    with st.expander(f"Issue {i}: Line {issue['line']}", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**❌ Found:**")
                            st.code(issue['found'], language="python")
                        
                        with col2:
                            st.markdown("**✅ Use instead:**")
                            st.code(issue['suggestion'], language="python")
                        
                        if issue.get('explanation'):
                            st.info(f"💡 {issue['explanation']}")
                        
                        st.caption(f"Type: {issue['type']} | Confidence: {issue['confidence']}")
                
                # AI Explanation
                if result.get('ai_explanation'):
                    st.divider()
                    st.subheader("🤖 AI Analysis")
                    st.markdown(result['ai_explanation'])
    
    with tab2:
        st.subheader("📚 Available Patterns")
        
        if st.session_state.assistant:
            patterns = st.session_state.assistant.patterns
            
            # Filter
            pattern_type = st.selectbox(
                "Filter by type",
                ["All"] + list(set([p.get('type', 'unknown') for p in patterns]))
            )
            
            filtered = patterns if pattern_type == "All" else [p for p in patterns if p.get('type') == pattern_type]
            
            st.write(f"Showing {len(filtered)} patterns")
            
            # Display patterns
            for i, pattern in enumerate(filtered[:20], 1):  # Limit display
                with st.expander(f"Pattern {i}: {pattern.get('type', 'unknown')}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Old:**")
                        st.code(pattern.get('old', pattern.get('old_style', 'N/A')), language="python")
                    
                    with col2:
                        st.markdown("**New:**")
                        st.code(pattern.get('new', pattern.get('new_style', 'N/A')), language="python")
                    
                    if pattern.get('explanation'):
                        st.info(pattern['explanation'])
    
    with tab3:
        st.subheader("🎓 Migration Guide")
        
        st.markdown("""
        ### Common Migration Patterns
        
        #### 1. Import Changes
        
        **OpenAI Models:**
        ```python
        # ❌ Old
        from langchain.llms import OpenAI
        from langchain.chat_models import ChatOpenAI
        
        # ✅ New
        from langchain_openai import OpenAI, ChatOpenAI
        ```
        
        #### 2. Chain Deprecations
        
        **LLMChain → LCEL:**
        ```python
        # ❌ Old
        from langchain.chains import LLMChain
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(input)
        
        # ✅ New
        chain = prompt | llm
        result = chain.invoke(input)
        ```
        
        #### 3. Document Loaders
        
        ```python
        # ❌ Old
        from langchain.document_loaders import TextLoader
        
        # ✅ New
        from langchain_community.document_loaders import TextLoader
        ```
        
        #### 4. Vector Stores
        
        ```python
        # ❌ Old
        from langchain.vectorstores import FAISS
        
        # ✅ New
        from langchain_community.vectorstores import FAISS
        ```
        
        ### Resources
        - [Official Migration Guide](https://python.langchain.com/docs/versions/migrating)
        - [LangChain Documentation](https://python.langchain.com/)
        - [LCEL Guide](https://python.langchain.com/docs/expression_language/)
        """)


if __name__ == "__main__":
    main()