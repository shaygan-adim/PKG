class GraphWriterAgent:
    """
    A non-LLM, procedural agent that takes structured outputs from other
    agents and executes the database commands to persist the knowledge.
    """

    def __init__(self, graph_db, vector_db, logger):
        self.graph_db = graph_db
        self.vector_db = vector_db
        self.logger = logger

    def run(self, node_id, extractor_output, linker_output, raw_text):
        """
        Executes the writing process.
        Args:
            node_id (str): The unique ID for the new node.
            extractor_output (dict): The structured data from the Extractor.
            linker_output (list): The list of relationships from the Linker.
            raw_text (str): The original user input.
        """
        try:
            # 1. Create the KnowledgeNode in Neo4j
            self.graph_db.create_knowledge_node(
                node_id=node_id,
                content_raw=raw_text,
                content_summary=extractor_output['content_summary'],
                node_type=extractor_output['node_type'],
                tags=extractor_output['tag_path']
            )

            # 2. Store the embedding in ChromaDB
            self.vector_db.add_embedding(
                node_id=node_id,
                text_to_embed=extractor_output['content_summary']
            )

            # 3. Create the relationships in Neo4j
            for rel in linker_output:
                self.graph_db.create_relationship(
                    from_node_id=node_id,
                    to_node_id=rel['to_node_id'],
                    rel_type=rel['type'],
                    description=rel['description']
                )
            
            print(f"GraphWriter successfully persisted node {node_id}.")

        except Exception as e:
            # Log the failure but don't raise, to avoid crashing the app
            print(f"GraphWriter Agent Error: {e}")
            self.logger.log_manual_action(
                action_name="write_failure",
                details=f"Failed to write node {node_id}. Error: {e}"
            )
