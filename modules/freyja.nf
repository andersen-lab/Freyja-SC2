process FREYJA_VARIANTS {
    publishDir "${params.output}/variants", mode: 'copy'

    input:
    tuple val(meta), path(bam)
    path reference

    output:
    tuple val(meta), path("${meta.id}_variants.tsv"), path("${meta.id}_depths.tsv")

    script:
    """
    freyja variants ${bam} --variants ${meta.id}_variants.tsv --depths ${meta.id}_depths.tsv --ref ${reference}
    samtools mpileup -aa -A -d 600000 -Q 0 -q 0 -B -f ${reference} ${bam} | cut -f1-4 > ${meta.id}_depths.tsv
    """
}

process FREYJA_DEMIX {
    publishDir "${params.output}/demix", mode: 'copy'
    //errorStrategy 'ignore' 

    input:
    tuple val(meta), path(variants), path(depths)
    path barcodes

    output:
    path "*.demixed"

    script:
    """
    freyja demix \\
        $variants \\
        $depths \\
        --barcodes $barcodes \\
        --output ${meta.id}.demixed \\
        --autoadapt
    """
}