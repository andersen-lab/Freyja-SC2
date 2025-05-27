/*
 *  Alignment and primer trimming
 */

process CUTADAPT_TRIM {
    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*_trimmed.fastq")

    script:
    if (reads.size() == 2) {
        """
        cutadapt -l +30 -l -30 -o ${meta.id}_1_trimmed.fastq -p ${meta.id}_2_trimmed.fastq ${reads[0]} ${reads[1]}
        """
    } else {
        """
        cutadapt -l +30 -l -30 -o ${meta.id}_trimmed.fastq ${reads}
        """
    }
}

process IVAR_TRIM {
    input:
    tuple val(meta), path(bam)
    path bedfiles

    output:
    tuple val(meta), path("*.trimmed.bam")

    script:
    """
    ivar trim -x 4 -e -m 80 -i ${bam} -b ${bedfiles}/${meta.primer_scheme}.bed | samtools sort -o ${meta.id}.trimmed.bam
    """
}

process MINIMAP2 {
    input:
    tuple val(meta), path(reads)
    path reference

    output:
    tuple val(meta), path("*.bam")

    script:
    if (reads.size() == 3) { // read.fastq, read1.fastq, read2.fastq
        """
        minimap2 \\
            -ax sr \\
            -t $task.cpus \\
            $reference \\
            ${reads[1]} ${reads[2]} \\
            | samtools view \\
                -bS \\
                | samtools sort \\
                    -o ${meta.id}.bam
        """
    } else { // either read.fastq or read1.fastq, read2.fastq
        """
        minimap2 \\
            -ax sr \\
            -t $task.cpus \\
            $reference \\
            $reads \\
            | samtools view \\
                -bS \\
                | samtools sort \\
                    -o ${meta.id}.bam
        """
    }
}