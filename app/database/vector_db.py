import chromadb
import google.generativeai as genai
import os

class VectorDBConnector:
    """Handles all interactions with the ChromaDB vector store."""

    def __init__(self, path, collection_name):
        """
        Initializes the connector and sets up the ChromaDB client and collection.
        Args:
            path (str): The directory to store the ChromaDB data.
            collection_name (str): The name of the collection to use.
        """
        try:
            # Configure the Gemini API key
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
            
            # No proxy code here. The global fix in app.py handles it.
            genai.configure(api_key=api_key)

            self.client = chromadb.PersistentClient(path=path)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"} # Use cosine distance for similarity
            )
            print("ChromaDB connection successful.")
        except Exception as e:
            print(f"Error connecting to ChromaDB: {e}")
            raise

    def _get_embedding(self, text):
        """
        Generates an embedding for a given text using the Gemini API.
        Args:
            text (str): The text to embed.
        Returns:
            list: The embedding vector.
        """
        if not text:
            return None
        # Use the 'text-embedding-004' model for generating embeddings
        result = genai.embed_content(model="models/text-embedding-004", content=text)
        return result['embedding']

    def add_embedding(self, node_id, text_to_embed):
        """
        Generates and stores an embedding for a knowledge node.
        Args:
            node_id (str): The unique ID of the node.
            text_to_embed (str): The text content (summary) to be embedded.
        """
        embedding = self._get_embedding(text_to_embed)
        if embedding:
            self.collection.add(
                embeddings=[embedding],
                metadatas=[{'node_id': node_id}],
                ids=[node_id]
            )

    def query_embeddings(self, query_text, n_results=5):
        """
        Performs a semantic search to find the most similar nodes.
        Args:
            query_text (str): The natural language query.
            n_results (int): The number of similar results to return.
        Returns:
            list: A list of dictionaries of the most similar nodes,
                  containing metadata and distance.
        """
        query_embedding = self._get_embedding(query_text)
        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        # The query returns a list of lists, we are interested in the first element
        return results['metadatas'][0] if results and results['metadatas'] else []

    def delete_embedding(self, node_id):
        """
        Deletes an embedding from the collection by its node_id.
        Args:
            node_id (str): The ID of the node whose embedding should be deleted.
        """
        self.collection.delete(ids=[node_id])
