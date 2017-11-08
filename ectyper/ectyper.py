#!/usr/bin/env python

"""
    Predictive genomics for _E. coli_ from the command line.
    Currently includes serotyping and VF finding.
"""
import logging
import os
import tempfile
import datetime

from ectyper import (blastFunctions, commandLineOptions, definitions,
                     genomeFunctions, loggingFunctions, predictionFunctions,
                     speciesIdentification)


LOG_FILE = loggingFunctions.initialize_logging()
LOG = logging.getLogger(__name__)

def run_program():
    """
    Wrapper for both the serotyping and virulence finder
    The program needs to do the following
    (1) Filter genome files based on format
    (2) Filter genome files based on species
    (3) Map FASTQ files to FASTA seq
    (1) Get names of all genomes being tested
    (2) Create a BLAST database of those genomes
    (3) Query for serotype and/or virulence factors
    (4) Parse the results
    (5) Display the results
    :return: success or failure

    """
    # Initialize the program
    LOG.info('Starting ectyper -- Serotype prediction. \
      Log file is: ' + str(LOG_FILE))
    args = commandLineOptions.parse_command_line()
    LOG.debug(args)

    ## Initialize temporary directories for the scope of this program
    with tempfile.TemporaryDirectory() as temp_dir:
        # Get the temporary files
        temp_files = create_tmp_files(temp_dir)
        LOG.info(temp_files)
        # Collect genome files
        LOG.info("Gathering genome files")
        raw_genome_files = genomeFunctions.get_files_as_list(args.input)
        LOG.debug(raw_genome_files)

        # Filter invalid file formats
        LOG.info("Start filtering based on file format")
        raw_fasta_files = []
        raw_fastq_files = []
        for file in raw_genome_files:
            file_format = genomeFunctions.get_valid_format(file)
            if file_format == 'fasta':
                raw_fasta_files.append(file)
            elif file_format == 'fastq':
                raw_fastq_files.append(file)
        LOG.debug('raw fasta files: %s', str(raw_fasta_files))
        LOG.debug('raw fastq files: %s', str(raw_fastq_files))

        # Filter invalid species
        LOG.info("Start filtering non-ecoli genome files")
        final_fasta_files = []
        for file in raw_fasta_files:
            filtered_file = filter_file_by_species(
                file, 'fasta', temp_files['assemble_temp_dir'])
            if filtered_file:
                final_fasta_files.append(filtered_file)
        for file in raw_fastq_files:
            filtered_file = filter_file_by_species(
                file, 'fastq', temp_files['assemble_temp_dir'])
            if filtered_file:
                final_fasta_files.append(filtered_file)

        LOG.info('%d final fasta files', len(final_fasta_files))
        if final_fasta_files == []:
            LOG.info("No valid genome file. Terminating the program.")
            exit(1)
        # Convert genome headers
        LOG.info("Start standardize genome headers")
        (all_genomes_list, all_genomes_files) = \
            genomeFunctions.get_genome_names_from_files(
                final_fasta_files, temp_files['fasta_temp_dir'])
        LOG.debug(all_genomes_list)
        LOG.debug(all_genomes_files)

        # Main prediction function
        predictions_file = run_prediction(
            all_genomes_files, args, temp_files['output_file'])
        # Add empty rows for genomes without blast result
        predictions_file = predictionFunctions.add_non_predicted(all_genomes_list, predictions_file)

        LOG.info('\nReporting result...')
        predictionFunctions.report_result(predictions_file)


def create_tmp_files(temp_dir):
    """
    Return a dictionary of temporary files used by ectyper
    Depending on whether legacy data is required or not
    """

    # Get the correct files and directories
    files_and_dirs = {
        'assemble_temp_dir':os.path.join(temp_dir, 'assemblies'),
        'fasta_temp_dir':os.path.join(temp_dir, 'fastas'),
    }

    output_file = os.path.join(
        definitions.WORKPLACE_DIR,
        'output',
        str(datetime.datetime.now().date()) + '_' + str(datetime.datetime.now().time()).replace(':', '.'),
        'output.csv')

    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)

    for d in [output_dir, files_and_dirs['assemble_temp_dir'],
              files_and_dirs['fasta_temp_dir']]:
        if not os.path.exists(d):
            os.makedirs(d)

    # Finalize the tmp_files dictionary
    files_and_dirs['output_file'] = output_file
    files_and_dirs['output_dir'] = output_dir

    LOG.info("Temporary files and directory created")
    return files_and_dirs
    

def run_prediction(genome_files, args, predictions_file):
    '''
    Core prediction functionality
    :param genome_files:
    :param args:
    :param predictions_file:
    :returns predictions_file
    '''
    query_file = definitions.SEROTYPE_FILE
    ectyper_dict_file = definitions.SEROTYPE_ALLELE_JSON
    # create a temp dir for blastdb
    with tempfile.TemporaryDirectory() as temp_dir:
        # Divide genome files into chunks of size 100
        chunk_size = 1000
        genome_chunks = [genome_files[i:i + chunk_size]
                        for i in range(0, len(genome_files), chunk_size)]
        for index, chunk in enumerate(genome_chunks):
            LOG.info("Start creating blast database #%d", index+1)
            blast_db = blastFunctions.create_blast_db(chunk, temp_dir)

            LOG.info("Start blast alignment on database #%d", index+1)
            blast_output_file = blastFunctions.run_blast(
                query_file, blast_db, args, len(chunk))
            LOG.info("Start serotype prediction for database #%d", index+1)
            predictions_file = predictionFunctions.predict_serotype(
                blast_output_file, ectyper_dict_file, predictions_file, args.verbose)
        return predictions_file

def filter_file_by_species(genome_file, genome_format, temp_dir, mash=False):
    '''
    Core species recognition functionality
    :param genome_file:
    :param genome_format:
    :param temp_dir:
    :param mash:
    :returns filtered_file
    '''
    combined_file = definitions.COMBINED
    filtered_file = None
    if genome_format is 'fastq':
        iden_file, pred_file = \
            genomeFunctions.assemble_reads(genome_file, combined_file, temp_dir)
        # If no alignment resut, the file is definitely not E.Coli
        if genomeFunctions.get_valid_format(iden_file) is None:
            LOG.warning("%s is filtered out because no identification alignment found", genome_file)
            return filtered_file
        if speciesIdentification.is_ecoli_genome(iden_file, genome_file, mash=mash):
            # final check before adding the alignment for prediction
            if genomeFunctions.get_valid_format(iden_file) != 'fasta':
                LOG.warning("%s is filtered out because no prediction alignment found", genome_file)
                return filtered_file
            filtered_file = pred_file
    if genome_format is 'fasta':
        if speciesIdentification.is_ecoli_genome(genome_file, mash=mash):
            filtered_file = genome_file
    return filtered_file
