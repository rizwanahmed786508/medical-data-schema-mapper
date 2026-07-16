# Medical Data Schema Mapper

AI-powered Streamlit application that automatically maps two different
medical CSV schemas into one standardized schema.

## Project Structure

```
schema_mapper_app/
├── app.py              # Streamlit frontend (UI, pages, sidebar)
├── utils.py            # Backend pipeline logic (ported 1:1 from the notebook)
├── style.css           # Premium dark-theme styling (glassmorphism, gradients)
├── requirements.txt    # Python dependencies
├── assets/             # Static assets
└── README.md
```

## Backend Logic

All AI/data logic in `utils.py` is a direct, unmodified port of the
original Jupyter Notebook:

1. CSV Reading
2. Data Standardization (alias dictionary + regex cleanup)
3. RapidFuzz Matching (diagnostic spelling similarity)
4. Sentence Transformer Embeddings (`all-MiniLM-L6-v2`)
5. Cosine Similarity
6. One-to-One Schema Mapping (thresholds: 0.70 Matched / 0.50 Review Required)
7. Mapping Validation
8. Data Quality Check
9. Data Cleaning (duplicates, missing values, IQR outlier clipping)
10. Data Transformation
11. CSV Output
12. JSON Report

No thresholds, formulas, or step ordering were changed — only wrapped
into reusable functions for the app.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage

1. Go to **New Output Generation** in the sidebar.
2. Upload your Source CSV and Target CSV.
3. Click **Generate Mapping** and wait for the pipeline to finish.
4. View results on the **Mapping Report** page.
5. Download the transformed CSV and the JSON mapping report.

## Notes

- The Sentence Transformer model is cached via `st.cache_resource`, so it
  only loads once per session.
- The first run will download the `all-MiniLM-L6-v2` model weights
  from Hugging Face (requires internet access).
