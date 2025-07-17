import os
import pandas as pd

metadata = pd.read_csv('data/all_metadata.tsv', index_col=None, low_memory=False, sep='\t')
metadata = metadata[metadata['sample_status'] == 'completed']
metadata = metadata[metadata['ww_surv_target_1_conc_unit'] == 'copies/l']

metadata['ww_surv_target_1_conc'] = metadata['ww_surv_target_1_conc'].apply(lambda x: pd.NA if x <= 0 else x)

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


# Rename columns
metadata = metadata.rename(
    columns={
        'accession': 'Accession',
        'collection_date': 'Collection_Date',
        'ww_population': 'ww_catchment_population',
        'ww_surv_target_1_conc': 'ww_viral_load',
    }
)

os.makedirs('outputs/aggregate', exist_ok=True)
metadata.to_csv('outputs/aggregate/aggregate_metadata.tsv', index=False, sep='\t')