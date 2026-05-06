# Data Science Final Project: Mobile Money Transaction Analysis and User Classification

## Group Members

- GHISLAIN CHE NGWATEH — ICTU20241769 — Group Lead
- TCHOUTO WANDJA ROSTANT — ICTU20233971
- NDAH RODIA ZONWUH — ICTU20234002
- NGEMINANG PRECIOUS — Matricule not visible in the shared member list

## Project Title

Mobile Money Transaction Analysis and User Classification

## Brief Description

This project analyzes mobile money SMS transaction data, cleans and structures the raw records, performs exploratory data analysis, and builds classification models to predict user activity level as Low, Medium, or High. The project combines behavioral transaction features and demographic information to understand user patterns and evaluate predictive performance.

## File Structure Explanation

- 2_Data_Cleaning/ — raw-to-cleaned data pipeline, cleaned datasets, and cleaning report
- 3_EDA/ — exploratory analysis notebook, EDA report, visualization folder, and explanation guide
- 4_Modeling/ — modeling notebook, pipeline script, saved model, comparison metrics, and results
- 5_Interpretation/ — interpretation notes and report summarizing findings and business meaning
- 5_Report/ — consolidated final report and appendices
- 6_Presentation/ — PowerPoint generation script and presentation slides
- Data/ — original raw files, extracted datasets, cleaned datasets, and model-ready outputs
- requirements.txt — Python dependencies required to reproduce the project

## How to Run the Code

1. Create and activate a Python virtual environment.
	python -m venv .venv
	.venv\Scripts\Activate.ps1

2. Install the project dependencies.
	pip install -r requirements.txt

3. Run the data cleaning pipeline.
	python 2_Data_Cleaning\data_pipeline.py

4. Run the modeling pipeline.
	python 4_Modeling\run_pipeline.py

5. Build the presentation slides.
	python 6_Presentation\build_presentation.py

6. Open the notebooks in VS Code or Jupyter if you want to inspect the analysis interactively.

## Dependencies / Requirements

The project uses pandas, numpy, matplotlib, seaborn, scikit-learn, xgboost, nbformat, python-pptx, openpyxl, notebook, ipykernel, joblib, and scipy. The complete list is recorded in requirements.txt.