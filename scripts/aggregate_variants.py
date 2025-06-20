"""
Aggregate iVar variants output from multiple samples into a single TSV file.
"""
import os
import pandas as pd

def main():
    MIN_DEPTH = 20  # Minimum coverage depth to consider a variant

    paths_list = [os.path.join('outputs/variants', fname) for fname in os.listdir('outputs/variants') if 'variants' in fname]
    variants_list = []

    for var_path in paths_list:
        try:
            df = pd.read_csv(var_path, sep='\t')
        except Exception:
            continue

        avg_qual = df['ALT_QUAL'].mean()
        freq_thresh = 10 ** (-avg_qual / 10)

        df = df[
            (df['ALT_FREQ'] > freq_thresh) &
            (df['ALT_DP'] >= MIN_DEPTH) &
            ((~df['ALT'].str.contains('[+-]')) | ((df['ALT'].str.len() - 1) % 3 == 0))
        ]

        if not df.empty:
            df['SRA'] = os.path.basename(var_path).split('.')[0]
            variants_list.append(df)

    # Concatenate all dataframes at once
    if variants_list:
        variants = pd.concat(variants_list, axis=0)
        os.makedirs('outputs/aggregate', exist_ok=True)
        variants.to_csv('outputs/aggregate/aggregate_variants.tsv', sep='\t', index=False)

if __name__ == '__main__':
    main()
