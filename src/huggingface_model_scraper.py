
import pandas as pd
from huggingface_hub import HfApi
from tqdm import tqdm

class HuggingFaceModelScraper:
    def __init__(self):
        """Initialize the Hugging Face API client."""
        self.api = HfApi()
        self.models = []
        self.processed_data = []

    def get_model_list(self):
        """Fetch the list of models from Hugging Face."""
        self.models = self.api.list_models()
        return self.models

    def process_models(self):
        """Extract relevant data from the list of models."""
        if not self.models:
            raise ValueError("No models found. Please run get_model_list first.")

        for model in tqdm(self.models, desc='Processing models', total=len(self.models)):
            self.processed_data.append({
                'id': model.id,
                'task': model.pipeline_tag,
                'created_at': model.created_at,
                'downloads': model.downloads,
                'downloads_all_time': model.downloads_all_time,
                'tags': model.tags,
                'likes': model.likes,
                'library_name': model.library_name,
                #'trending_score': model.trending_score,
            })

    @staticmethod
    def get_config(model_id):
        try:
            config = AutoConfig.from_pretrained(model_id)
            return config.to_json_string()
        except:
            return None

    @staticmethod    
    def get_readme(model_id):
        try:
            readme = hf_hub_download(model_id, filename='README.md')
            return readme
        except:
            return None

    def to_dataframe(self):
        """Convert the processed data into a pandas DataFrame."""
        if not self.processed_data:
            raise ValueError("No processed data found. Please run process_models first.")

        return pd.DataFrame(self.processed_data)


# Example usage (comment out for use as a library):
# if __name__ == "__main__":
#     scraper = HuggingFaceModelScraper()
#     scraper.get_model_list()
#     scraper.process_models()
#     df = scraper.to_dataframe()
#     df.to_csv("huggingface_models.csv", index=False)
