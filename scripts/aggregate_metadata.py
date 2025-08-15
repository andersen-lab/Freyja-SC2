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

# Create metadata json
metadata = pd.read_csv('data/all_metadata.tsv', index_col=None, low_memory=False, sep='\t')
metadata = metadata[metadata['accession'].isin(accessions)]
metadata = metadata[['accession', 'collection_date', 'geo_loc_country', 'geo_loc_region', 'ww_population', 'collected_by', 'ww_surv_target_1_conc','ww_surv_target_1_conc_unit', 'collection_site_id']]
metadata = metadata.rename(columns={
    'accession':'Accession',
    'collection_date':'Collection_Date',
    'ww_surv_target_1_conc':'viral_load',
    'ww_surv_target_1_conc_unit':'viral_load_unit'}
)
metadata['ww_population'] = metadata['ww_population'].fillna(-1.0)
metadata = metadata.drop_duplicates(subset='Accession', keep='first')


# Check if demix output exists and has coverage > 0
metadata['demix_success'] = metadata['Accession'].isin(demix_success)
agg_demix = pd.read_json('outputs/aggregate/aggregate_demix_new.json', orient='records', lines=True).drop_duplicates(subset='Accession', keep='first')

try:
    metadata['demix_success'] = metadata['sra_accession'].isin(agg_demix['sra_accession']) & (metadata['sra_accession'].isin(demix_success))
except:
    metadata['demix_success'] = False

agg_variants = pd.read_json('outputs/aggregate/aggregate_variants_new.json', orient='records', lines=True).drop_duplicates(subset='sra_accession', keep='first')


try:
    metadata['variants_success'] = metadata['sra_accession'].isin(agg_variants['sra_accession'])
except KeyError:
    metadata['variants_success'] = False

# if variants_success is false, set demix_success to false
metadata['demix_success'] = np.where(metadata['variants_success']==False, False, metadata['demix_success'])

metadata['coverage_intervals'] = metadata['sra_accession'].apply(get_intervals)
metadata['coverage_intervals'] = metadata['coverage_intervals'].apply(format_intervals)

os.makedirs('outputs/aggregate', exist_ok=True)
metadata.to_csv('outputs/aggregate/aggregate_metadata.tsv', index=False, sep='\t')