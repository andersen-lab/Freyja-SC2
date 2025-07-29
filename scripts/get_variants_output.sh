# for accession in data/samples_to_rerun.csv, copy {accession}_variants.tsv and {accession}_depths.tsv demix_rerun/

while read -r accession; do
    gsutil stat gs://outbreak-ww-data/variants/${accession}_variants.tsv
    if [ $? -ne 0 ]; then
        echo "gs://outbreak-ww-data/variants/${accession}_variants.tsv does not exist"
        continue
    fi
    gcloud storage cp gs://outbreak-ww-data/variants/${accession}_variants.tsv demix_rerun/
    gcloud storage cp gs://outbreak-ww-data/variants/${accession}_depths.tsv demix_rerun/
done < "data/samples_to_rerun.csv"