import pandas as pd
import os

STATE_TO_REGION = {
    'Connecticut': 'Northeast', 'Maine': 'Northeast', 'Massachusetts': 'Northeast', 'New Hampshire': 'Northeast', 
    'Rhode Island': 'Northeast', 'Vermont': 'Northeast', 'New Jersey': 'Northeast', 'New York': 'Northeast', 
    'Pennsylvania': 'Northeast', 'Illinois': 'Midwest', 'Indiana': 'Midwest', 'Michigan': 'Midwest', 
    'Ohio': 'Midwest', 'Wisconsin': 'Midwest', 'Iowa': 'Midwest', 'Kansas': 'Midwest', 'Minnesota': 'Midwest', 
    'Missouri': 'Midwest', 'Nebraska': 'Midwest', 'North Dakota': 'Midwest', 'South Dakota': 'Midwest', 
    'Delaware': 'South', 'Maryland': 'South', 'Florida': 'South', 'Georgia': 'South', 'North Carolina': 'South', 
    'South Carolina': 'South', 'Virginia': 'South', 'District of Columbia': 'South', 'West Virginia': 'South', 
    'Alabama': 'South', 'Kentucky': 'South', 'Mississippi': 'South', 'Tennessee': 'South', 'Arkansas': 'South', 
    'Louisiana': 'South', 'Oklahoma': 'South', 'Texas': 'South', 'Arizona': 'West', 'Colorado': 'West', 
    'Idaho': 'West', 'Montana': 'West', 'Nevada': 'West', 'New Mexico': 'West', 'Utah': 'West', 'Wyoming': 'West', 
    'Alaska': 'West', 'California': 'West', 'Hawaii': 'West', 'Oregon': 'West', 'Washington': 'West'
}

metadata = pd.read_csv('data/all_metadata.tsv', index_col=None, low_memory=False, sep='\t')
metadata = metadata[metadata['sample_status'] == 'completed']

# omit ENA samples for now
metadata = metadata[~metadata['accession'].str.startswith('ERR')]

# drop invalid viral load
metadata['ww_surv_target_1_conc'] = metadata.apply(
    lambda row: pd.NA if row['ww_surv_target_1_conc_unit'] != 'copies/l' else row['ww_surv_target_1_conc'], axis=1
)
metadata['ww_surv_target_1_conc'] = metadata['ww_surv_target_1_conc'].apply(lambda x: pd.NA if pd.notna(x) and x <= 0 else x)

metadata = metadata[metadata['geo_loc_country'] == 'USA']
metadata['census_region'] = metadata['geo_loc_region'].map(STATE_TO_REGION)
metadata['Geographic_Location'] = metadata['geo_loc_country'] + '/' + metadata['geo_loc_region']
metadata = metadata[metadata['Geographic_Location'].notna()]

# Select relevant columns 
metadata = metadata[
    [
        'accession', 
        'collection_date', 
        'Geographic_Location',
        'census_region',
        'ww_population', 
        'collected_by', 
        'ww_surv_target_1_conc', 
        'collection_site_id'
    ]
]
#Isolate_Source', 'Bioprojects', 'population', 'Biosample', 'ReleaseDate', 'site_id', 'Virus_OrganismName', 'UpdateDate', 'Isolate_Name', 'census_region', 'Host_OrganismName', 'Length', 'Geographic_Location', 'Accession', 'viral_load', 'Collection_Date'
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

os.makedirs('muninn_sc2_input', exist_ok=True)
metadata.to_csv('muninn_sc2_input/aggregate_metadata.tsv', index=False, sep='\t')