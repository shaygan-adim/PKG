import google.generativeai as genai
import json
import yaml
import os

class ExtractorAgent:
    """
    Takes raw text, understands it, and structures it into a JSON object
    containing a summary, node_type, and tag_path.
    """

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config['llm']
        self.prompt_template = config['prompts']['extractor']
        
        # No proxy code here. The global fix in app.py handles it.
        self.model = genai.GenerativeModel(
            self.config['model_name'],
            generation_config=self.config['generation_config']
        )

    def _update_tags_if_needed(self, tag_path, current_tags):
        """Checks if a new tag was created and updates the hierarchy."""
        temp_dict = current_tags
        path_changed = False
        for i, key in enumerate(tag_path):
            if i == len(tag_path) - 1: # Last element is the specific tag (a list item)
                if key not in temp_dict:
                    temp_dict.append(key)
                    path_changed = True
            else: # It's a dictionary key
                if key not in temp_dict:
                    # Create the rest of the path
                    temp_dict[key] = {}
                    path_changed = True
                temp_dict = temp_dict[key]
        
        return current_tags if path_changed else None

    def run(self, user_text, tags_config):
        """
        Executes the agent's logic.
        Args:
            user_text (str): The raw text input from the user.
            tags_config (dict): The current tag hierarchy from tags.yaml.
        Returns:
            tuple: A tuple containing the structured JSON output and potentially
                   the updated tags configuration.
        """
        prompt = self.prompt_template.format(
            user_text=user_text,
            tag_hierarchy=yaml.dump(tags_config)
        )
        
        try:
            response = self.model.generate_content(prompt)
            # Clean the response to extract only the JSON part
            cleaned_response_text = response.text.strip().lstrip("```json").rstrip("```")
            structured_data = json.loads(cleaned_response_text)
            
            self.logger.log_api_call(
                agent_name="Extractor",
                prompt=prompt,
                response=cleaned_response_text,
                status="success"
            )

            # Check if the agent created a new tag and update the config
            new_tags_config = self._update_tags_if_needed(structured_data['tag_path'], tags_config)
            
            return structured_data, new_tags_config

        except Exception as e:
            self.logger.log_api_call(
                agent_name="Extractor",
                prompt=prompt,
                response=str(e),
                status="error"
            )
            print(f"Extractor Agent Error: {e}")
            raise
