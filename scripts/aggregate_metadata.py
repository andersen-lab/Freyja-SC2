import os
import pandas as pd

metadata = pd.read_csv('data/all_metadata.tsv', index_col=None, low_memory=False, sep='\t')
metadata = metadata[metadata['sample_status'] == 'completed']

metadata['ww_surv_target_1_conc'] = metadata.apply(
    lambda row: pd.NA if row['ww_surv_target_1_conc_unit'] != 'copies/l' else row['ww_surv_target_1_conc'], axis=1
)

metadata['ww_surv_target_1_conc'] = metadata['ww_surv_target_1_conc'].apply(lambda x: pd.NA if pd.notna(x) and x <= 0 else x)

metadata['Geographic_Location'] = metadata['geo_loc_country'] + '/' + metadata['geo_loc_region']

# Select relevant columns 
metadata = metadata[
    [
        'accession', 
        'collection_date', 
        'Geographic_Location',
        'ww_population', 
        'collected_by', 
        'ww_surv_target_1_conc', 
        'collection_site_id'
    ]
]

# add empty columns for future use
for col in ['Biosample', 'ReleaseDate', 'Isolate_Source', 'Length', 'UpdateDate', 'Isolate_Name', 'Bioprojects', 'Host_OrganismName']:
    metadata[col] = pd.NA

metadata['Virus_OrganismName'] = 'SARS-CoV-2'

# Rename columns
metadata = metadata.rename(
    columns={
        'accession': 'Accession',
        'collection_date': 'Collection_Date',
        'ww_population': 'population',
        'ww_surv_target_1_conc': 'viral_load',
        'collection_site_id': 'site_id',
    }
)

os.makedirs('outputs/aggregate', exist_ok=True)
metadata.to_csv('outputs/aggregate/aggregate_metadata.tsv', index=False, sep='\t')