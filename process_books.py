from src.ocr import parse_pdf
from src.preprocessing import clean_az_text

from tqdm import tqdm
import os
import json
import pandas as pd

if __name__ == '__main__':
    dest_dir: str = 'content'
    base_dir: str = 'docs'

    df = pd.read_csv('docs/metadata.csv')

    for i, row in tqdm(df.iterrows(), total=len(df)):
        full_path: str = row['Full_Path']
        doc_id: str = row['Doc_id']
        category: str = row['Category']

        category = category.lower()

        os.makedirs(
            os.path.join(dest_dir, category),
            exist_ok=True
        )

        dest_path = os.path.join(dest_dir, category, doc_id) + '.json'

        page_data = parse_pdf(full_path)

        for id in range(len(page_data)):
            page_entry = page_data[id]
            page_entry['content'] = clean_az_text(page_entry['content'])

            page_data[id] = page_entry
        
        with open(dest_path, 'w') as f:
            json.dump(page_data, f, indent=4)
        