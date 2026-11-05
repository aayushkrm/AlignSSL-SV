# Notes on files in this directory

This directory contains all the files related to the giggles genotyping of 967 samples on the augmented graph HPRC_mg_44+966.

- giggles-panel-multiallelic.vcf.gz
    - produced by rule annotate_panel_giggles_ready of snakemake_pipelines/post-augmentation-genotyping/rules/prepare-vcf.smk in https://github.com/marschall-lab/project-ont-1kg.
    - used by the giggles genotyping script as input as list of sites to genotype.

- giggles-panel-biallelic.vcf.gz
    - produced by rule annotate_panel_giggles_ready of snakemake_pipelines/post-augmentation-genotyping/rules/prepare-vcf.smk in https://github.com/marschall-lab/project-ont-1kg.
    - it is the biallelic version of giggles-panel-multiallelic.vcf.gz.

- giggles-genotypes-multiallelic.vcf.gz
    - multisample multiallelic raw genotypes produced by giggles.
    - contains all the sites from the giggles-panel-multiallelic.vcf.gz but some do not have genotypes.
    - produced by rule merge_vcf_to_multisample of snakemake_pipelines/post-augmentation-genotyping/rules/genotyping.smk in https://github.com/marschall-lab/project-ont-1kg.

- giggles-genotypes-biallelic.vcf.gz
    - biallelic decomposition of giggles-genotypes-multiallelic.vcf.gz
    - produced by rule convert_multisample_vcf_biallelic of snakemake_pipelines/post-augmentation-genotyping/rules/genotyping.smk in https://github.com/marschall-lab/project-ont-1kg

- giggles-genotypes-biallelic.ac0-filtered.vcf.gz
    - filtered out the AC=0 variants from the giggles-genotypes-biallelic.vcf.gz

- final-vcf.unphased.vcf.gz
    - further filtering of the genotypes of giggles-genotypes-biallelic.ac0-filtered.vcf.gz as described under "Graph-aware genotyping with Giggles" of the methods section.
