import os
import pandas as pd

metadata = pd.read_csv('all_metadata.tsv', index_col=None, low_memory=False, sep='\t')
metadata = metadata[metadata['sample_status'] == 'completed']

# omit ENA samples and limit to USA for now
metadata = metadata[~metadata['accession'].str.startswith('ERR')]
metadata = metadata[metadata['geo_loc_country'] == 'USA']
metadata['Geographic_Location'] = metadata['geo_loc_country'] + '/' + metadata['geo_loc_region']
metadata = metadata[metadata['Geographic_Location'].notna()]

# drop invalid viral load
metadata['ww_surv_target_1_conc'] = metadata.apply(
    lambda row: pd.NA if row['ww_surv_target_1_conc_unit'] != 'copies/l' else row['ww_surv_target_1_conc'], axis=1
)
metadata['ww_surv_target_1_conc'] = metadata['ww_surv_target_1_conc'].apply(lambda x: pd.NA if pd.notna(x) and x <= 0 else x)

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

# empty string columns
for col in ['Biosample', 'Isolate_Source', 'Isolate_Name', 'Bioprojects', 'Virus_OrganismName', 'Host_OrganismName']:
    metadata[col] = 'NA'

# empty date columns
for col in ['ReleaseDate', 'UpdateDate']:
    metadata[col] = pd.to_datetime("1970-01-01")

# empty integer columns
for col in ['Length']:
    metadata[col] = 0

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