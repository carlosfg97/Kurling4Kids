# Kurling4Kids
McGill MMA BUSA649 Community Capstone Project. Client: Kurling4Kids

# File index

### PDF Extract
* **pdfextract_v1.ipynb:** A PDF extract script takes data from the main PDF (REP-EDC-2020_Fusion_Final) and extracts it to a .xlsx format.
* **dataCleaningPDFextract.ipynb:** This script reads from the extracted excels (organizations & foundations) and cleans column names, address, other attributes to prepare it for analysis

### past_donors
* **past_donors_etl.ipynb:** Reads the excel with past donors information, standarizes the fields and concatenates into a single dataset
* **past_donors_analysis.ipynb:** Performs descriptive analysis *(Analysis 1)* with the past donors information. 

### dataset_merge
* **merge_donors_organizations.ipynb:** Reads the extracted datasets from the previous scripts and merges them based on fuzzy matching of company names. Certain input files are used to decide which company names are equivalent based on client's knowledge.
* **matched_donors_analysis.ipynb:** Once organizations (PDF source) and donors (K4K source) are merged, we perform descriptive analysis *(Analysis 2)* of the donors that appear in the PDF (matched donors), which are 61 organizations in total. This time we aim to exploit the PDF attributes.



