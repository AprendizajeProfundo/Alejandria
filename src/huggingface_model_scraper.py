import pandas as pd
from huggingface_hub import HfApi
from tqdm import tqdm
from transformers import AutoConfig
from joblib import Parallel, delayed
import multiprocessing

class HuggingFaceModelScraper:
    def __init__(self, previous_data):
        """Initialize the Hugging Face API client."""
        self.api = HfApi()
        self.models = []
        self.processed_data = []
        self.previous_data = previous_data

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
                'tags': model.tags,
                'likes': model.likes,
                'library_name': model.library_name,
            })

    @staticmethod
    def get_config(model_id):
        try:
            config = AutoConfig.from_pretrained(model_id)
            return config.to_json_string()
        except Exception:
            return None

    @staticmethod
    def get_readme(model_id):
        from huggingface_hub import hf_hub_download

        try:
            readme_path = hf_hub_download(repo_id=model_id, filename='README.md')
            with open(readme_path, 'r') as file:
                return file.read()
        except Exception:
            return None
        
    def parallel_get_config(self, data):
        num_cores = multiprocessing.cpu_count()
        results = Parallel(n_jobs=num_cores)(delayed(self.get_config)(model) for model in tqdm(data['id'], desc='Getting config files', total=len(data)))
        return results

    def parallel_get_readme(self, data):
        num_cores = multiprocessing.cpu_count()
        results = Parallel(n_jobs=num_cores)(delayed(self.get_readme)(model) for model in tqdm(data['id'], desc='Getting readmes', total=len(data)))
        return results

    def to_dataframe(self):
        """Convert the processed data into a pandas DataFrame."""
        if not self.processed_data:
            raise ValueError("No processed data found. Please run process_models first.")

        return pd.DataFrame(self.processed_data)

def main(input_path, output_path):
    # Load previous data if available
    try:
        previous_data = pd.read_csv(input_path)
    except FileNotFoundError:
        previous_data = pd.DataFrame(columns=['id'])

    scraper = HuggingFaceModelScraper(previous_data=previous_data)

    # Step 1: Get the list of models
    scraper.get_model_list()

    # Step 2: Process the models
    scraper.process_models()
    new_data = scraper.to_dataframe()

    # Step 3: Identify new models
    new_models = new_data[~new_data['id'].isin(previous_data['id'])]

    if new_models.empty:
        print("No new models to process.")
        return

    # Step 4: Fetch config and README files in parallel
    configs = scraper.parallel_get_config(new_models)
    readmes = scraper.parallel_get_readme(new_models)

    # Step 5: Add config and README to the data
    new_models['config'] = configs
    new_models['readme'] = readmes

    # Step 6: Combine new data with previous data
    combined_data = pd.concat([previous_data, new_models], ignore_index=True)

    # Step 7: Save the updated data
    combined_data.to_csv(output_path, index=False)
    print("Data updated and saved.")

if __name__ == "__main__":
    main()
