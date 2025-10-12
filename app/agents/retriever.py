class HybridRetrieverAgent:
    """
    A non-LLM, procedural agent that performs a hybrid search across the
    vector database (for semantic similarity) and the graph database (for
    direct tag matches).
    """

    def __init__(self, graph_db, vector_db):
        self.graph_db = graph_db
        self.vector_db = vector_db

    def run(self, semantic_query, graph_tags):
        """
        Executes the hybrid retrieval process.
        Args:
            semantic_query (str): The query optimized for vector search.
            graph_tags (list): A list of tags to search for directly.
        Returns:
            list: A de-duplicated list of relevant KnowledgeNode dictionaries.
        """
        retrieved_ids = set()

        # 1. Vector Search
        if semantic_query:
            vector_results_meta = self.vector_db.query_embeddings(semantic_query, n_results=10)
            for meta in vector_results_meta:
                retrieved_ids.add(meta['node_id'])

        # 2. Graph Traversal (Tag Search)
        if graph_tags:
            for tag in graph_tags:
                graph_results = self.graph_db.search_nodes_by_tag(tag)
                for node in graph_results:
                    retrieved_ids.add(node['node_id'])
        
        # 3. Fetch full node data for all unique IDs using the efficient method
        if not retrieved_ids:
            return []
            
        final_nodes = self.graph_db.get_nodes_by_ids(list(retrieved_ids))

        print(f"Retriever found {len(final_nodes)} relevant nodes.")
        return final_nodes
