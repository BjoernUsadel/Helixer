#! /usr/bin/env python3
import os
import yaml
import argparse
import tempfile
import subprocess
from pprint import pprint
from geenuff2h5 import ParameterParser


if __name__ == '__main__':
    """
    pp = ParameterParser(config_file_path='config/helixer_config.yaml')
    pp.io_group.add_argument('--config-path', type=str, default='config/helixer_config.yaml',
                             help='Config in form of a YAML file with lower priority than parameters given on the command line.')
    pp.io_group.add_argument('--fasta-path', type=str, default=None, required=True
                             help='Directly convert from a FASTA file to .h5')
    pp.io_group.add_argument('--species', type=str, default='', help='Species name.')
    pp.data_group.add_argument('--species-category', type=str, default='vertebrate', choices=['vertebrate', 'land_plant', 'fungi'],
                               help='What model to use for the annotation. (Default is "vertebrate".)'

    pp.post_group = parser.add_argument_group("Post processing parameters")
    pp.post_group.add_argument('--window-size', type=int, default=100, help='')
    pp.post_group.add_argument('--edge-threshold', type=float, default=0.1, help='')
    pp.post_group.add_argument('--peak-threshold', type=float, default=0.8, help='')
    pp.post_group.add_argument('--min-coding-length', type=int, default=100, help='')
    args = get_and_check_args(export_parser_base)
    """

    pp = ParameterParser(config_file_path='config/helixer_config.yaml')
    pp.io_group.add_argument('--config-path', type=str, default='config/helixer_config.yaml',
                             help='Config in form of a YAML file with lower priority than parameters given on the command line.')
    pp.io_group.add_argument('--fasta-path', type=str, required=True
                             help='Directly convert from a FASTA file to .h5')
    pp.io_group.add_argument('--species', type=str, help='Species name.')
    pp.data_group.add_argument('--species-category', type=str, choices=['vertebrate', 'land_plant', 'fungi'],
                               help='What model to use for the annotation. (Default is "vertebrate".)'

    pp.post_group = parser.add_argument_group("Post processing parameters")
    pp.post_group.add_argument('--window-size', type=int, help='')
    pp.post_group.add_argument('--edge-threshold', type=float, help='')
    pp.post_group.add_argument('--peak-threshold', type=float, help='')
    pp.post_group.add_argument('--min-coding-length', type=int, help='')

    helixer_defaults = {
        'fasta_path': '',
        'species': '',
        'species_category': 'vertebrate',
        'window_size': 100,
        'edge_threshold': 0.1,
        'peak_threshold': 0.8,
        'min_coding_length': 100
    }
    pp.defaults = {**pp.defaults, **helixer_defaults}

    args = pp.get_args()

    # generate the .h5 file in a temp dir, which is then deleted
    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_genome_h5_path = os.path.join(tmp_dirname, f'tmp_species_{args.species}.h5')
        tmp_pred_h5_path = os.path.join(tmp_dirname, f'tmp_predictions_{args.species}.h5')

        controller = HelixerFastaToH5Controller(args.fasta_path, tmp_genome_h5_path)
        controller.export_fasta_to_h5(chunk_size=args.chunk_size, compression=args.compression,
                                      multiprocess=not args.no_multiprocess, species=args.species)

        # hardcoded model dir path, probably not optimal
        model_filepath = os.path.join('models', f'{species_category}.h5')
        assert os.path.isfile(model_filepath), f'{model_filepath} does not exists'

        # calls to HybridModel.py and to HelixerPost, both have to be in PATH
        hybrid_model_out = subprocess.run([
            'python', 'HybridModel.py',
            '--load-model-path', model_filepath,
            '--test-data', tmp_genome_h5_path,
            '--prediction-output-path', tmp_pred_h5_path,
        ]

        if hybrid_model_out == 0:
            print('\n Model predictions successful. \n')
        else:
            print('\n An error occured during model prediction. Exiting.\n')
            exit()

        HelixerPost <genome.h5> <predictions.h5> <windowSize> <edgeThresh> <peakThresh> <minCodingLength> <gff>
        helixerpost_out = subprocess.run([
            'python', 'HybridModel.py',
            '--load-model-path', model_filepath,
            '--test-data', tmp_genome_h5_path,
            '--prediction-output-path', tmp_pred_h5_path,
        ]

        if helixerpost_out == 0:
            print('\n Model predictions successful. \n')
        else:
            print('\n An error occured during model prediction. Exiting.\n')
            exit()




