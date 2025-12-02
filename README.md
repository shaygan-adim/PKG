## PKG – Personal Knowledge Graph

PKG is a **personal knowledge management assistant** built on top of a knowledge graph, semantic search, and LLM-powered agents. It lets you capture ideas, link them together, and query them later through a clean Streamlit UI.

### High-Level Features

- **Web UI (Streamlit)**: Single-page interface with sections for adding knowledge, querying the graph, managing nodes, and viewing system status.
- **Knowledge Graph Storage**: Uses Neo4j to store knowledge nodes, their summaries, tags, and relationships.
- **Vector Search**: Uses ChromaDB and Gemini embeddings for semantic retrieval of relevant knowledge.
- **Audit Logging**: Logs all LLM calls and key actions into SQLite for traceability.

### Core Agents & Responsibilities

- **Extractor Agent**: Takes raw text and produces a structured summary, node type, and hierarchical tags (optionally extending the tag tree).
- **Knowledge Linker Agent**: Finds related existing nodes via vector search and proposes relationships between them and the new node.
- **Graph Writer Agent**: Persists new knowledge into Neo4j and ChromaDB, creating nodes, embeddings, and relationships.
- **Query Analyzer Agent**: Turns a natural-language question into a semantic query plus graph tags for hybrid retrieval.
- **Hybrid Retriever Agent**: Combines vector similarity search with graph lookups to gather the most relevant nodes.
- **Synthesizer Agent**: Uses the retrieved context to generate a final answer, citing the nodes it used.

### End-to-End Knowledge Pipeline

- **Add Knowledge**
  - User submits free-form text in the UI.
  - Extractor structures it and updates the tag hierarchy if needed.
  - Linker suggests connections to existing nodes.
  - Writer creates/updates graph nodes, relationships, and embeddings.

- **Query the Graph**
  - User asks a question in chat.
  - Query Analyzer prepares a semantic query and tags.
  - Hybrid Retriever pulls relevant nodes from the graph and vector store.
  - Synthesizer produces a markdown answer grounded in the retrieved context.

- **Manage & Inspect**
  - Search and delete specific nodes from the graph.
  - Visualize the full knowledge graph.
  - Inspect the current tag hierarchy and review LLM/API logs.

### Running the Stack (Overview)

- **Dependencies**: Docker, Docker Compose, and a valid `GEMINI_API_KEY` environment variable.
- **Configuration**: Adjust `config.yaml` and `tags.yaml` as needed; ensure Neo4j credentials in `config.yaml` match `docker-compose.yaml`.
- **Start**: From the project root, bring up the services with Docker Compose, then open the Streamlit UI in your browser on the exposed port.


