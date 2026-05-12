# CS-4824 Machine Learning Final Project: Insider Trading Anomaly Detection

## Team Members:
Alex Sleptsov, Nikita Sukharevich, Vissu Manchem

## Project Overview

This project implements a Machine Learning pipeline for Anomaly Detection, specifically targeting Insider Trading activities within financial/cryptocurrency networks.

By analyzing behavioral patterns and transaction data associated with entities (such as proxy_wallets), the model identifies outliers that exhibit characteristics commonly associated with illicit or insider trading. The notebook encompasses the end-to-end data science lifecycle, including:

1. Environment Setup & Dependency Installation
2. Data Preprocessing & Cleaning
3. Feature Engineering & Scaling
4. Anomaly Detection Model Implementation
5. Evaluation and Visualizations (e.g., Archetype Heatmaps using Z-scores to profile anomalous wallets)

## Files Included in this ZIP:
- ML_final_project.ipynb: The main Jupyter Notebook containing all properly commented, executable code.
- iran_trade_data.csv: The primary trade dataset required to run the notebook.
- iran_user_data.csv: The user dataset required to run the notebook.
- README.md: This documentation file.

## Link to the Website 

Note that you will need to be signed into a VT account to view this:\
https://sites.google.com/vt.edu/polymarket-insider-trading/home

## Instructions to Run the Code

This code was originally developed and tested in Google Colab, so it must be run in a Colab environment.

### Step 1: Set up the Environment

Navigate to Google Colab.

Click File > Upload notebook and upload the ML_final_project.ipynb file.

### Step 2: Upload datasets

On the left sidebar of your Google Colab workspace, click the Folder icon (Files).

Upload both iran_trade_data.csv and iran_user_data.csv into the base /content/ directory. (These were in the ZIP folder)

### Step 3: Execute the Pipeline

Go to Runtime > Run all in the top menu bar to execute the entire pipeline sequentially.
