"""
Aggregate iVar variants output from multiple samples into a single TSV file.
"""
import argparse
import os

import pandas as pd

def accession_from_variants_filename(path):
    base = os.path.basename(path)
    if base.endswith('_variants.tsv'):
        return base[:-len('_variants.tsv')]
    return base.split('_')[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--input-dir',
        required=True,
        help='Directory containing *_variants.tsv and *_depths.tsv',
    )
    parser.add_argument(
        '-o', '--output-dir',
        required=True,
        help='Directory for aggregated variants_sc2.tsv output',
    )
    args = parser.parse_args()

    variants_dir = args.input_dir
    paths_list = [
        os.path.join(variants_dir, fname)
        for fname in os.listdir(variants_dir)
        if 'variants' in fname
    ]
    variants_list = []

    for var_path in paths_list:
        try:
            df = pd.read_csv(var_path, sep='\t')
            df = df[
                ((~df['ALT'].str.contains('[+-]')) | ((df['ALT'].str.len() - 1) % 3 == 0))
            ]

        except Exception:
            continue

        if not df.empty:
            df['SRA'] = accession_from_variants_filename(var_path)
            variants_list.append(df.copy())

    if variants_list:
        variants = pd.concat(variants_list, axis=0)
        os.makedirs(args.output_dir, exist_ok=True)
        variants.to_csv(
            os.path.join(args.output_dir, 'variants_sc2.tsv'),
            sep='\t',
            index=False,
        )


if __name__ == '__main__':
    main()
