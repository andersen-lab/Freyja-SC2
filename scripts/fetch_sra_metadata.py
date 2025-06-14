from datetime import timedelta, datetime
import pandas as pd
import re
from Bio import Entrez
import xml.etree.ElementTree as ET
import http.client
import urllib.error
import hashlib
import time

us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}

START_DATE = '2020-03-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')
INTERVAL = 14 # days

def md5_hash(string):
    hex = hashlib.md5(string.encode('utf-8')).hexdigest()[:4]
    return str(int(hex, 16))


def parse_collection_date(x):
    # If collection_date is in the format '20XX-XX-XX/20XX-XX-XX', take the second date
    if re.match(r'\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}', x):
        return x.split('/')[0]

    # If " 00:00:00+00:00" is present, remove it
    x = re.sub(r' 00:00:00\+00:00', '', x)

    return x

def get_metadata():

    date_ranges = [((datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=(i-1)*INTERVAL)).strftime('%Y-%m-%d'), 
               (datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=i*INTERVAL)).strftime('%Y-%m-%d')) 
               for i in range(1, int((datetime.strptime(END_DATE, '%Y-%m-%d') - datetime.strptime(START_DATE, '%Y-%m-%d')).days/INTERVAL) + 1)]
    metadata = pd.DataFrame()
    for date_range in date_ranges:
        print(date_range)

        start_dt = datetime.strptime(date_range[0], '%Y-%m-%d').date()
        end_dt = datetime.strptime(date_range[1], '%Y-%m-%d').date()

        delta = timedelta(days=1)
        dates = []
        while start_dt <= end_dt:
            dates.append(start_dt.isoformat() + '[All Fields]')
            start_dt += delta

        date_str = ' OR '.join(dates)

        search_term = (
            '((Wastewater[All Fields] OR wastewater metagenome[All Fields]) AND '
            '("Severe acute respiratory syndrome coronavirus 2"[Organism] OR '
            'SARS-CoV-2[All Fields]) AND '
            f'({date_str}))'
        )

        Entrez.email = "jolevy@scripps.edu"
        try:
            handle = Entrez.esearch(db="sra", idtype='acc', retmax=4000,
                                    sort='recently_added',
                                    term=search_term)
        except urllib.error.HTTPError as e:
            # Retry once
            print('HTTPError, retrying')
            time.sleep(10)
            handle = Entrez.esearch(db="sra", idtype='acc', retmax=4000,
                                    sort='recently_added',
                                    term=search_term)

        record = Entrez.read(handle)
        handle.close()

        try:
            handle = Entrez.efetch(
                db="sra", id=record['IdList'], rettype="gb", retmode='text')
        except urllib.error.HTTPError as e:
            # Retry once
            print('HTTPError, retrying')
            time.sleep(10)
            handle = Entrez.efetch(
                db="sra", id=record['IdList'], rettype="gb", retmode='text')

        try:
            string = handle.read()
        except (http.client.IncompleteRead) as e:
            string = e.partial
        handle.close()

        returned_meta = str(string, 'UTF-8')

        with open("data/NCBI_metadata.xml", "w") as f:
            f.write(returned_meta)

        try:
            root = ET.fromstring(returned_meta)
        except:
            continue

        allDictVals = {}

        for root0 in root:
            # pull all sample attributes
            vals = [r.text for r in root0.findall('.//SAMPLE_ATTRIBUTE/')]
            # sampExp = [r.text for r in root0.findall(
            #     './/EXPERIMENT/IDENTIFIERS/PRIMARY_ID')]
            seq_meta = [r.text for r in root0.findall(
                './/RUN_SET/RUN/RUN_ATTRIBUTES/RUN_ATTRIBUTE/')]
            sampID = [r.text for r in root0.findall(
                './/RUN_SET/RUN/IDENTIFIERS/PRIMARY_ID')]
            runAttributes = [r.attrib for r in root0.findall('.//RUN_SET/RUN')]
            
            
            if len(sampID) > 1:
                print('more than one experiment... add funcs')
            elif len(sampID) == 0:
                continue
            else:
                sampID = sampID[0]
            # write to dictionary form
            try:
                dictVals = {vals[i].replace(' ', '_'): vals[i+1]
                            for i in range(0, len(vals), 2)}
                for i in range(0, len(seq_meta), 2):
                    dictVals[seq_meta[i].replace(' ', '')] = seq_meta[i+1]
            except:
                continue
            dictVals['experiment_id'] = sampID
            dictVals['SRA_id'] = root0[0].attrib['accession']
            dictVals['SRA_published_date'] = runAttributes[0]['published'].split(' ')[0]
            try:
                allDictVals[sampID] = dictVals
            except:
                continue

        metadata = pd.concat([metadata, pd.DataFrame(allDictVals).T], axis=0)
    return metadata


def main():
    metadata = get_metadata()
    metadata.to_csv('data/raw_metadata.csv')
    metadata = pd.read_csv('data/raw_metadata.csv', index_col=0 ,low_memory=False)
    metadata.index.name = 'accession'
    metadata = metadata[~metadata.index.duplicated(keep='first')]

    
    print('SRA accessions:', metadata.index.str.contains('SRR').sum())
    print('ENA accessions:',metadata.index.str.contains('ERR').sum())
    print('Total : ', len(metadata))

    # Get sample status from current metadata file

    old_metadata = pd.read_csv('data/all_metadata.tsv', index_col=0, low_memory=False, sep='\t')
    sample_status = old_metadata['sample_status']

    all_metadata = metadata.join(sample_status, how='left')
    
    # Combine old and new metadata and remove duplicates
    all_metadata = pd.concat([old_metadata, all_metadata], axis=0)
    all_metadata = all_metadata[~all_metadata.index.duplicated(keep='first')]

    all_metadata['sample_status'] = all_metadata['sample_status'].fillna('to_run')

    all_metadata.index.name = 'accession'
    all_metadata = all_metadata[~all_metadata.index.duplicated(keep='first')]
    print('All fetched samples: ', len(all_metadata))

    
    # Parse collection date
    all_metadata['collection_date'] = all_metadata['collection_date'].astype(str)
    all_metadata['collection_date'] = all_metadata['collection_date'].apply(parse_collection_date)
    all_metadata['collection_date'] = pd.to_datetime(all_metadata['collection_date'], format='%Y-%m-%d', errors='coerce')
    all_metadata = all_metadata[~all_metadata['collection_date'].isna()]

    # Parse location information
    ## Combine ENA country column with SRA country column
    
    all_metadata['geo_loc_name'] = all_metadata['geo_loc_name'].fillna(all_metadata['geographic_location_(country_and/or_sea)'])
    all_metadata = all_metadata[~all_metadata['geo_loc_name'].isna()]

    all_metadata['geo_loc_country'] = all_metadata['geo_loc_name'].apply(
    lambda x: x.split(':')[0].strip() if ':' in x else x)
    all_metadata['geo_loc_region'] = all_metadata['geo_loc_name'].apply(
        lambda x: x.split(':')[1].strip() if len(x.split(':')) > 1 else '')
    all_metadata['geo_loc_region'] = all_metadata['geo_loc_region'].apply(
        lambda x: x.split(',')[0].strip() if len(x.split(',')) > 1 else x)
    all_metadata['geo_loc_region'] = all_metadata['geo_loc_region'].fillna(all_metadata['geographic_location_(region_and_locality)'])
   
    if 'US Virgin Islands' in all_metadata['geo_loc_region'].unique():
        all_metadata['geo_loc_region'] = all_metadata['geo_loc_region'].replace(
            'US Virgin Islands', 'U.S. Virgin Islands')
        
    print('Samples with valid location: ', len(all_metadata))

    # Parse population size
    all_metadata['ww_population'] = all_metadata['ww_population'].fillna(
        all_metadata['population_size_of_the_catchment_area']) # for ENA

    all_metadata['ww_population'] = pd.to_numeric(all_metadata['ww_population'], errors='coerce')
    all_metadata = all_metadata[~all_metadata['ww_population'].isna()]

    print('Samples with valid population: ', len(all_metadata))

    # Parse primer scheme
    PRIMER_SCHEMA = {
        'v5.3': 'ARTICv5.3.2',
        'v4.1': 'ARTICv4.1',
        'v3': 'ARTICv3',
        'qiaseq': 'ARTICv3',
        'snap': 'snap_primers'
    }

    def match_primer_scheme(primer_str):
        if pd.isna(primer_str):
            return 'unknown'
        primer_lower = str(primer_str).strip().lower()
        for key, value in PRIMER_SCHEMA.items():
            if key in primer_lower:
                return value        
        return 'unknown'

    all_metadata['amplicon_PCR_primer_scheme'] = all_metadata['amplicon_PCR_primer_scheme'].apply(match_primer_scheme)

    # Select columns of interest
    all_metadata = all_metadata[['amplicon_PCR_primer_scheme', 'collected_by', 'sequenced_by',
                                 'geo_loc_name', 'geo_loc_country', 'geo_loc_region', 'collection_date', 'SRA_published_date', 'ww_population', 'ww_surv_target_1_conc','ww_surv_target_1_conc_unit', 'sample_status']]

    # Keep samples with missing viral load, set to -1.0 to work with Elasticsearch
    all_metadata['ww_surv_target_1_conc'] = pd.to_numeric(all_metadata['ww_surv_target_1_conc'], errors='coerce')
    all_metadata['ww_surv_target_1_conc_unit'] = all_metadata['ww_surv_target_1_conc_unit'].str.lower()
    all_metadata['ww_surv_target_1_conc_unit'] = all_metadata['ww_surv_target_1_conc_unit'].fillna(-1.0)
    all_metadata['ww_surv_target_1_conc'] = all_metadata['ww_surv_target_1_conc'].fillna(
        -1.0)
    # if units column contains 'copies/ml', convert concentration to copies/l
    mask = all_metadata['ww_surv_target_1_conc_unit'].str.contains('copies/ml', na=False)
    all_metadata.loc[mask, 'ww_surv_target_1_conc'] *= 1000
    all_metadata.loc[mask, 'ww_surv_target_1_conc_unit'] = 'copies/l'


    # If unit contains the substring 'copies/g', set unit to 'copies/g'
    all_metadata.loc[all_metadata['ww_surv_target_1_conc_unit'].str.contains('copies/g', na=False), 'ww_surv_target_1_conc_unit'] = 'copies/g'
    all_metadata.loc[all_metadata['ww_surv_target_1_conc_unit'].str.contains('copies/l', na=False), 'ww_surv_target_1_conc_unit'] = 'copies/l'

    print('Samples with valid viral load',len(all_metadata[all_metadata['ww_surv_target_1_conc'] > 0]))

    
    # For NA values of collected_by, fill with sequenced_by
    all_metadata['collected_by'] = all_metadata['collected_by'].fillna(all_metadata['sequenced_by'])
    
    # Create human-readable, unique site_id for each sample
    all_metadata['collection_site_id'] = all_metadata['geo_loc_name'].fillna('') +\
        all_metadata['ww_population'].fillna('').astype(str) +\
        all_metadata['amplicon_PCR_primer_scheme'].fillna('unknown') +\
        all_metadata['collected_by'].fillna('').astype(str)


    all_metadata['collection_site_id'] = all_metadata['collection_site_id'].apply(md5_hash)
    all_metadata['collection_site_id'] = all_metadata['geo_loc_country'] + '_' + all_metadata['geo_loc_region'].apply(
        lambda x: us_state_to_abbrev[x] if x in us_state_to_abbrev else x) + '_' + all_metadata['collection_site_id']

    # Select samples to run
    all_metadata['sample_status'] = all_metadata['sample_status'].fillna('to_run')
    samples_to_run = all_metadata[all_metadata['sample_status'] == 'to_run']
    print('All samples: ', all_metadata['sample_status'].value_counts())
    print('Samples to run: ', len(samples_to_run))

    # Sort by collection date
    all_metadata = all_metadata.sort_values(by='collection_date', ascending=False)
    all_metadata.index.name = 'accession'

    all_metadata.to_csv('data/all_metadata.tsv', sep='\t')


if __name__ == "__main__":
    main()
