import streamlit as st
import yaml
import uuid
from datetime import datetime
import os
import ssl
import urllib.request

# --- PAGE CONFIGURATION (Moved to top) ---
st.set_page_config(
    page_title="KAI - Personal Knowledge AI",
    page_icon="🧠",
    layout="wide",
)

# --- ROBUST PROXY FIX & UI DEBUGGER ---
# 1. Disable SSL verification globally for proxy compatibility.
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 2. Definitive HTTP Proxy Connection Test with UI Output
st.sidebar.title("System Diagnostics")
proxy_env = os.getenv("HTTPS_PROXY")
if not proxy_env:
    st.sidebar.warning("Proxy NOT Configured\n(HTTPS_PROXY variable is not set)")
else:
    st.sidebar.info(f"Proxy found: `{proxy_env}`")
    with st.sidebar.expander("Run Proxy Test", expanded=True):
        with st.spinner("Testing proxy connection..."):
            try:
                proxy_handler = urllib.request.ProxyHandler({'https': proxy_env})
                opener = urllib.request.build_opener(proxy_handler)
                urllib.request.install_opener(opener)
                
                with urllib.request.urlopen("https://ifconfig.me/ip", timeout=15) as response:
                    if response.getcode() == 200:
                        external_ip = response.read().decode('utf-8').strip()
                        st.success("Proxy connection is working!")
                        st.caption(f"Public IP via proxy: `{external_ip}`")
                    else:
                        st.error(f"Proxy Test Failed\n(Status Code: {response.getcode()})")
            except Exception as e:
                st.error("Proxy Test Failed")
                st.caption(f"Error: {e}")
# ------------------------------------


# Import database connectors
from database.log_db import SQLiteLogger
from database.graph_db import GraphDBConnector
from database.vector_db import VectorDBConnector

# Import agent pipelines
from agents.extractor import ExtractorAgent
from agents.linker import KnowledgeLinkerAgent
from agents.writer import GraphWriterAgent
from agents.query_analyzer import QueryAnalyzerAgent
from agents.retriever import HybridRetrieverAgent
from agents.synthesizer import SynthesizerAgent

# For graph visualization
from streamlit_agraph import agraph, Node, Edge, Config

# --- STATE MANAGEMENT ---
# Initialize session state variables to preserve them across reruns.
if 'db_connections_established' not in st.session_state:
    st.session_state.db_connections_established = False
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# --- DATABASE & AGENT INITIALIZATION ---
@st.cache_resource
def load_configs():
    """Loads configuration files."""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('tags.yaml', 'r') as f:
        tags = yaml.safe_load(f)
    return config, tags

@st.cache_resource
def initialize_connectors(_config):
    """Initializes and caches database connectors."""
    try:
        log_db = SQLiteLogger(_config['databases']['sqlite']['path'])
        graph_db = GraphDBConnector(
            uri=_config['databases']['neo4j']['uri'],
            user=_config['databases']['neo4j']['user'],
            password=_config['databases']['neo4j']['password']
        )
        vector_db = VectorDBConnector(
            path=_config['databases']['chromadb']['path'],
            collection_name=_config['databases']['chromadb']['collection_name']
        )
        return log_db, graph_db, vector_db
    except Exception as e:
        st.error(f"Fatal Error: Could not connect to databases. Please check logs. Error: {e}")
        st.stop()

def initialize_agents(_config, _log_db, _graph_db, _vector_db):
    """Initializes agents with necessary dependencies."""
    extractor = ExtractorAgent(_config, _log_db)
    linker = KnowledgeLinkerAgent(_config, _log_db, _vector_db)
    writer = GraphWriterAgent(_graph_db, _vector_db, _log_db)
    query_analyzer = QueryAnalyzerAgent(_config, _log_db)
    retriever = HybridRetrieverAgent(_graph_db, _vector_db)
    synthesizer = SynthesizerAgent(_config, _log_db)
    return extractor, linker, writer, query_analyzer, retriever, synthesizer

# Load configurations and initialize components
config, tags_config = load_configs()
log_db, graph_db, vector_db = initialize_connectors(config)
extractor, linker, writer, query_analyzer, retriever, synthesizer = initialize_agents(
    config, log_db, graph_db, vector_db
)

# --- UI HELPER FUNCTIONS ---
def display_graph(graph_data):
    """Renders the knowledge graph using streamlit-agraph."""
    if not graph_data or not graph_data['nodes']:
        st.warning("Graph is empty. Add some knowledge to see it here.")
        return

    nodes = [Node(id=n['node_id'], label=n.get('content_summary', 'No Summary'), shape="box", title=f"Type: {n.get('node_type', 'N/A')}\nTags: {n.get('tags', [])}") for n in graph_data['nodes']]
    edges = [Edge(source=r['source'], target=r['target'], label=r.get('type', 'RELATES_TO')) for r in graph_data['relationships']]

    # Configure graph appearance
    agraph_config = Config(width='100%',
                           height=600,
                           directed=True,
                           physics=True,
                           hierarchical=False,
                           nodeHighlightBehavior=True,
                           highlightColor="#F7A7A6",
                           collapsible=True,
                           )

    agraph(nodes=nodes, edges=edges, config=agraph_config)

def update_tags_file(new_tags_config):
    """Writes the updated tag hierarchy back to the YAML file."""
    with open('tags.yaml', 'w') as f:
        yaml.dump(new_tags_config, f, default_flow_style=False, sort_keys=False)


# --- MAIN APPLICATION UI ---
st.title("🧠 KAI: Your Personal Knowledge AI")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Add Knowledge", "Query Graph", "Manage Knowledge", "System Status"])

# --- PAGE 1: ADD KNOWLEDGE ---
if page == "Add Knowledge":
    st.header("Add New Knowledge")
    st.markdown("Enter any piece of information—an idea, a fact, a lesson—and KAI's agents will process and connect it.")

    with st.form("new_knowledge_form", clear_on_submit=True):
        new_text = st.text_area("Enter your knowledge here:", height=150)
        submitted = st.form_submit_button("Add to my Brain")

    if submitted and new_text:
        with st.status("🤖 Agents at work...", expanded=True) as status:
            try:
                # 1. Extractor Agent
                st.write("Step 1: The Extractor is analyzing and structuring the text...")
                extractor_output, new_tags_config = extractor.run(new_text, tags_config)
                if new_tags_config:
                    update_tags_file(new_tags_config)
                    tags_config = new_tags_config # Update in-memory config
                    st.success("Extractor finished. New tags were added to your hierarchy!")
                else:
                    st.success("Extractor finished.")

                # 2. Linker Agent
                st.write("Step 2: The Knowledge Linker is searching for connections...")
                new_node_id = str(uuid.uuid4())
                linker_output = linker.run(new_node_id, extractor_output['content_summary'])
                st.success(f"Linker found {len(linker_output)} potential connections.")

                # 3. Writer Agent
                st.write("Step 3: The Graph Writer is saving everything to the databases...")
                writer.run(new_node_id, extractor_output, linker_output, new_text)
                st.success("Writer finished. Knowledge is now part of your graph!")

                status.update(label="✅ Knowledge successfully added!", state="complete")

            except Exception as e:
                st.error(f"An error occurred in the pipeline: {e}")
                status.update(label="Pipeline failed.", state="error")

# --- PAGE 2: QUERY GRAPH ---
elif page == "Query Graph":
    st.header("Query Your Knowledge Graph")
    st.markdown("Ask a question in natural language. KAI will search your graph and synthesize an answer.")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 KAI is thinking..."):
                try:
                    # 1. Query Analyzer
                    analyzer_output = query_analyzer.run(prompt)

                    # 2. Hybrid Retriever
                    retrieved_nodes = retriever.run(
                        analyzer_output['semantic_query'],
                        analyzer_output['graph_tags']
                    )

                    if not retrieved_nodes:
                        response = "I couldn't find any relevant information in your knowledge graph to answer that question."
                        st.warning(response)
                    else:
                        # 3. Synthesizer
                        response = synthesizer.run(prompt, retrieved_nodes)
                        st.markdown(response)

                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

                except Exception as e:
                    response = f"Sorry, an error occurred while processing your request: {e}"
                    st.error(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

# --- PAGE 3: MANAGE KNOWLEDGE ---
elif page == "Manage Knowledge":
    st.header("Manage & Delete Knowledge")
    st.markdown("Search for specific nodes and remove them if they are no longer needed.")

    search_term = st.text_input("Search for a node by content:")
    if search_term:
        results = graph_db.search_nodes_by_content(search_term)

        if not results:
            st.info("No matching nodes found.")
        else:
            st.write(f"Found {len(results)} matching nodes:")
            for node in results:
                with st.expander(f"**{node.get('content_summary', 'Node')}** `(ID: ...{node['node_id'][-6:]})`"):
                    st.write(f"**Raw Content:** {node.get('content_raw', 'N/A')}")
                    st.write(f"**Type:** {node.get('node_type', 'N/A')}")
                    st.write(f"**Tags:** {node.get('tags', [])}")
                    st.write(f"**Created:** {node.get('created_at', 'N/A')}")

                    if st.button("Delete this Node", key=f"delete_{node['node_id']}"):
                        try:
                            # Perform the cascading delete
                            graph_db.delete_node(node['node_id'])
                            vector_db.delete_embedding(node['node_id'])
                            log_db.log_manual_action("delete_node", f"Deleted node {node['node_id']}")
                            st.success(f"Successfully deleted node {node['node_id']}.")
                            # Use rerun to refresh the search results
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete node: {e}")

# --- PAGE 4: SYSTEM STATUS ---
elif page == "System Status":
    st.header("System Status & Information")

    tab1, tab2, tab3 = st.tabs(["📊 Knowledge Graph", "🏷️ Tag Hierarchy", "📜 API Logs"])

    with tab1:
        st.subheader("Full Knowledge Graph")
        st.markdown("An interactive visualization of all your knowledge nodes and their relationships.")
        if st.button("Render/Refresh Graph"):
            st.session_state.show_graph = True
            with st.spinner("Loading graph data..."):
                st.session_state.graph_data = graph_db.get_full_graph()

        if st.session_state.show_graph:
            display_graph(st.session_state.graph_data)

    with tab2:
        st.subheader("Current Tag Hierarchy")
        st.markdown("This is the `tags.yaml` file that the Extractor agent uses and updates.")
        st.json(tags_config)

    with tab3:
        st.subheader("Gemini API Call Logs")
        st.markdown("A complete audit trail of all calls made to the Gemini API by the agents.")
        logs = log_db.get_all_logs()
        if logs:
            # Display logs in a pandas DataFrame for better formatting
            import pandas as pd
            df = pd.DataFrame(logs)
            # Reorder columns for clarity
            df = df[['timestamp', 'agent_name', 'status', 'prompt', 'response', 'id']]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No API calls have been logged yet.")
