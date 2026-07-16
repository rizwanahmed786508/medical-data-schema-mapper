"""
utils.py
==========================================================
Medical Data Schema Mapper — Backend Pipeline
==========================================================

This module contains the EXACT backend logic from the original
Jupyter Notebook, reorganized into reusable functions so it can
be called from the Streamlit app. No algorithmic changes were
made — thresholds, formulas, and step order are preserved as-is.

Pipeline:
    1. Standardize column names (alias dictionary + regex cleanup)
    2. RapidFuzz spelling-similarity scores (supporting/diagnostic only)
    3. Sentence-Transformer embeddings (semantic meaning)
    4. Cosine similarity matrix
    5. One-to-one schema mapping (greedy, highest score first)
    6. Data quality check
    7. Data cleaning (duplicates, missing values, outliers via IQR)
    8. Data transformation into the target schema
    9. Transformation verification
    10. JSON mapping report
==========================================================
"""

import re
import json

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


# ==========================================================
# STEP 1: Alias Dictionary
# (identical to the notebook's ALIAS_DICT)
# ==========================================================

ALIAS_DICT = {
    "mr no": "medical record number",
    "mr#": "medical record number",
    "mr number": "medical record number",

    "pt": "patient",
    "pt age": "patient age",
    "pt gender": "patient gender",

    "o2 sat": "oxygen saturation",
    "spo2": "oxygen saturation",

    "hr": "heart rate",

    "bp": "blood pressure",

    "hba1c": "hemoglobin a1c",

    "doc": "doctor",
    "physician": "doctor",

    "cell no": "phone number",
    "mobile no": "phone number",

    "blood sugar": "glucose",

    "sex": "gender",

    "patient id": "record id",
}


# ==========================================================
# STEP 2: Load the Sentence Transformer model (cached)
# ==========================================================

@st.cache_resource(show_spinner=False)
def load_model():
    """Load the sentence-transformer model once and cache it across reruns."""
    return SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================================
# STEP 3: Standardize Column Names
# ==========================================================

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip punctuation, collapse whitespace, then apply the
    alias dictionary to normalize column names — identical to the notebook."""
    df = df.copy()

    df.columns = (
        df.columns
        .str.lower()
        .str.replace("_", " ", regex=False)
        .str.replace("-", " ", regex=False)
        .str.replace(r"[^a-z0-9 ]", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    df.columns = [ALIAS_DICT.get(col, col) for col in df.columns]

    return df


# ==========================================================
# STEP 4: RapidFuzz Similarity (supporting / diagnostic score)
# ==========================================================

def compute_rapidfuzz_matrix(source_columns, target_columns) -> pd.DataFrame:
    """Returns a DataFrame of RapidFuzz spelling-similarity scores.
    Rows = source columns, Columns = target columns.
    This mirrors the notebook's diagnostic RapidFuzz step — it is
    informational only and is NOT used to decide the final mapping
    (the notebook explicitly relies on semantic/cosine similarity
    for the final decision)."""
    data = []
    for source_col in source_columns:
        row = {}
        for target_col in target_columns:
            row[target_col] = round(fuzz.ratio(source_col, target_col), 2)
        data.append(row)

    return pd.DataFrame(data, index=source_columns)


# ==========================================================
# STEP 5 & 6: Embeddings + Cosine Similarity
# ==========================================================

def compute_similarity_matrix(model, source_columns, target_columns):
    """Generate sentence-transformer embeddings for both column lists
    and return the cosine similarity matrix (source x target)."""
    source_embeddings = model.encode(source_columns)
    target_embeddings = model.encode(target_columns)

    similarity_matrix = cosine_similarity(source_embeddings, target_embeddings)
    return similarity_matrix


# ==========================================================
# STEP 7: One-to-One Schema Mapping
# ==========================================================

def generate_mapping(source_columns, target_columns, similarity_matrix) -> pd.DataFrame:
    """Greedy one-to-one mapping: for every source column, pick the
    best-scoring, not-yet-used target column. Status thresholds:
        Matched          -> score >= 0.70
        Review Required  -> 0.50 <= score < 0.70
        Low Confidence    -> score < 0.50
    This is an exact port of the notebook's mapping loop."""
    mapping = []
    used_targets = set()

    for i in range(len(source_columns)):
        source = source_columns[i]
        scores = similarity_matrix[i]
        sorted_index = scores.argsort()[::-1]

        for index in sorted_index:
            target = target_columns[index]
            score = scores[index]

            if target not in used_targets:
                if score >= 0.70:
                    status = "Matched"
                elif score >= 0.50:
                    status = "Review Required"
                else:
                    status = "Low Confidence"

                mapping.append({
                    "Source Column": source,
                    "Target Column": target,
                    "Similarity Score": round(float(score), 3),
                    "Status": status,
                })

                used_targets.add(target)
                break

    return pd.DataFrame(mapping)


# ==========================================================
# STEP 8: Data Quality Check
# ==========================================================

def data_quality_report(df: pd.DataFrame) -> dict:
    """Shape, dtypes, missing values, and duplicate row count for a dataset."""
    return {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }


# ==========================================================
# STEP 9: Data Cleaning
# ==========================================================

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, fill missing values (median/mode), trim & lowercase
    text, clip numeric outliers via IQR, and reset the index.
    Identical logic to the notebook's clean_dataset()."""
    df = df.drop_duplicates()

    numeric_columns = df.select_dtypes(include="number").columns
    df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())

    text_columns = df.select_dtypes(include="object").columns
    if len(text_columns) > 0:
        df[text_columns] = df[text_columns].fillna(df[text_columns].mode().iloc[0])

    for column in text_columns:
        df[column] = df[column].str.strip()

    for column in text_columns:
        df[column] = df[column].str.lower()

    for column in numeric_columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        lower_limit = Q1 - (1.5 * IQR)
        upper_limit = Q3 + (1.5 * IQR)

        df[column] = df[column].clip(lower_limit, upper_limit)

    df.reset_index(drop=True, inplace=True)

    return df


# ==========================================================
# STEP 10: Data Transformation
# ==========================================================

def transform_data(mapping_df: pd.DataFrame, source_df: pd.DataFrame) -> pd.DataFrame:
    """Build the transformed dataset using the target schema's column names,
    populated from the mapped source columns. Only 'Matched' and
    'Review Required' mappings are transformed — 'Low Confidence'
    mappings are skipped, exactly as in the notebook."""
    transformed_df = pd.DataFrame()

    for i in range(len(mapping_df)):
        source_column = mapping_df.loc[i, "Source Column"]
        target_column = mapping_df.loc[i, "Target Column"]
        status = mapping_df.loc[i, "Status"]

        if status != "Low Confidence":
            if source_column in source_df.columns:
                transformed_df[target_column] = source_df[source_column]

    return transformed_df


# ==========================================================
# STEP 11: Verify Transformation
# ==========================================================

def verify_transformation(target_df: pd.DataFrame, transformed_df: pd.DataFrame) -> bool:
    """Checks whether the transformed dataset's columns match the target
    schema's columns exactly (order included), as in the notebook."""
    return list(target_df.columns) == list(transformed_df.columns)


# ==========================================================
# STEP 12: JSON Mapping Report
# ==========================================================

def generate_json_report(mapping_df: pd.DataFrame, source_columns, target_columns) -> dict:
    """Builds the same summary JSON structure as the notebook's final step."""
    matched = (mapping_df["Status"] == "Matched").sum()
    review = (mapping_df["Status"] == "Review Required").sum()
    low = (mapping_df["Status"] == "Low Confidence").sum()

    mapping_report = {
        "Total Source Columns": len(source_columns),
        "Total Target Columns": len(target_columns),
        "Total Mappings": len(mapping_df),
        "Matched": int(matched),
        "Review Required": int(review),
        "Low Confidence": int(low),
        "Average Similarity Score": round(mapping_df["Similarity Score"].mean(), 3),
        "Mapping Details": mapping_df.to_dict(orient="records"),
    }

    return mapping_report


# ==========================================================
# ORCHESTRATOR
# Runs the full pipeline end-to-end (used by the Streamlit page).
# Each step is yielded as (progress_fraction, label, payload) so the
# UI can update a progress bar / status text as it runs.
# ==========================================================

def run_full_pipeline(source_df_raw: pd.DataFrame, target_df_raw: pd.DataFrame):
    """Generator that runs the entire notebook pipeline step by step and
    yields progress updates. The final yield contains the complete
    results dictionary."""

    results = {}

    # Step 1: quality check on raw data
    yield 0.05, "Checking source & target data quality...", None
    results["raw_source_quality"] = data_quality_report(source_df_raw)
    results["raw_target_quality"] = data_quality_report(target_df_raw)

    # Step 2: standardize column names
    yield 0.15, "Standardizing column names...", None
    source_df = standardize_columns(source_df_raw)
    target_df = standardize_columns(target_df_raw)
    results["source_columns"] = source_df.columns.tolist()
    results["target_columns"] = target_df.columns.tolist()

    # Step 3: RapidFuzz (diagnostic)
    yield 0.30, "Running RapidFuzz spelling similarity...", None
    results["rapidfuzz_matrix"] = compute_rapidfuzz_matrix(
        results["source_columns"], results["target_columns"]
    )

    # Step 4: Sentence Transformer + Cosine similarity
    yield 0.45, "Generating semantic embeddings (Sentence Transformer)...", None
    model = load_model()
    similarity_matrix = compute_similarity_matrix(
        model, results["source_columns"], results["target_columns"]
    )
    results["similarity_df"] = pd.DataFrame(
        similarity_matrix,
        index=results["source_columns"],
        columns=results["target_columns"],
    )

    # Step 5: One-to-one mapping
    yield 0.60, "Computing cosine similarity & building schema mapping...", None
    mapping_df = generate_mapping(
        results["source_columns"], results["target_columns"], similarity_matrix
    )
    results["mapping_df"] = mapping_df

    # Step 6: Data cleaning
    yield 0.75, "Cleaning datasets (duplicates, missing values, outliers)...", None
    source_df_clean = clean_dataset(source_df)
    target_df_clean = clean_dataset(target_df)
    results["source_df_clean"] = source_df_clean
    results["target_df_clean"] = target_df_clean

    # Step 7: Transformation
    yield 0.88, "Transforming source data into the target schema...", None
    transformed_df = transform_data(mapping_df, source_df_clean)
    results["transformed_df"] = transformed_df
    results["transformation_ok"] = verify_transformation(target_df_clean, transformed_df)

    # Step 8: JSON report
    yield 0.97, "Generating JSON mapping report...", None
    results["json_report"] = generate_json_report(
        mapping_df, results["source_columns"], results["target_columns"]
    )

    yield 1.0, "Done!", results
