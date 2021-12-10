#! /usr/bin/env python3
import os
import yaml
import argparse
import tempfile
import subprocess
from pprint import pprint

from geenuff2h5 import ParameterParser
from helixer.export.exporter import HelixerExportController, HelixerFastaToH5Controller


class HelixerParameterParser(ParameterParser):
    def __init__(self, config_file_path=''):
        super().__init__(config_file_path)
        pp.io_group.add_argument('--fasta-path', type=str, required=True,
                                 help='Directly convert from a FASTA file to .h5')
        pp.io_group.add_argument('--gff-output-path', type=str, required=True, help='Output GFF file path.')
        pp.io_group.add_argument('--species', type=str, help='Species name.')

        pp.data_group.add_argument('--chunk-input-len', type=int,
                                   help='How to chunk up the genomic sequence. Should grow with average gene length.')
        pp.data_group.add_argument('--species-category', type=str, choices=['vertebrate', 'land_plant', 'fungi'],
                                   help='What model to use for the annotation. (Default is "vertebrate".)')

        pp.post_group = pp.parser.add_argument_group("Post processing parameters")
        pp.post_group.add_argument('--window-size', type=int, help='')
        pp.post_group.add_argument('--edge-threshold', type=float, help='')
        pp.post_group.add_argument('--peak-threshold', type=float, help='')
        pp.post_group.add_argument('--min-coding-length', type=int, help='')

        helixer_defaults = {
            'fasta_path': '',
            'species': '',
            'chunk_input_len': 19440,
            'species_category': 'vertebrate',
            'window_size': 100,
            'edge_threshold': 0.1,
            'peak_threshold': 0.8,
            'min_coding_length': 100
        }
        pp.defaults = {**pp.defaults, **helixer_defaults}

    @staticmethod
    def check_args(args):
        model['/model_weights/dense_1/dense_1/bias:0'].shape[0]
        assert args.h5_output_path.endswith('.h5'), '--output-path must end with ".h5"'


if __name__ == '__main__':
    pp = HelixerParameterParser('config/helixer_config.yaml')
    args = pp.get_args()

    # generate the .h5 file in a temp dir, which is then deleted
    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_genome_h5_path = os.path.join(tmp_dirname, f'tmp_species_{args.species}.h5')
        tmp_pred_h5_path = os.path.join(tmp_dirname, f'tmp_predictions_{args.species}.h5')

        controller = HelixerFastaToH5Controller(args.fasta_path, tmp_genome_h5_path)
        # hard coded chunk size due to how the models have been created
        controller.export_fasta_to_h5(chunk_size=args.chunk_input_len, compression=args.compression,
                                      multiprocess=not args.no_multiprocess, species=args.species)

        # hard coded model dir path, probably not optimal
        model_filepath = os.path.join('models', f'{args.species_category}.h5')
        assert os.path.isfile(model_filepath), f'{model_filepath} does not exists'

        # calls to HybridModel.py and to HelixerPost, both have to be in PATH
        hybrid_model_out = subprocess.run([
            'HybridModel.py', '--verbose',
            '--load-model-path', model_filepath,
            '--test-data', tmp_genome_h5_path,
            '--prediction-output-path', tmp_pred_h5_path,
        ])

        if hybrid_model_out != 0:
            print('\n An error occured during model prediction. Exiting.')
            # do not exit explicitely to remove tmp files
        else:
            print('\n Model predictions successful.')
            helixerpost_cmd = ['helixer_post_bin', tmp_genome_h5_path, tmp_pred_h5_path]
            helixerpost_params = [args.window_size, args.edge_threshold, args.peak_threshold, args.min_coding_length]
            helixerpost_cmd += [str(e) for e in helixerpost_params] + [args.output_path]

            helixerpost_out = subprocess.run(helixerpost_cmd)
            if helixerpost_out == 0:
                print(f'\n Helixer successfully finished and GFF written to {output_path}.')
            else:
                print('\n An error occured during post processing.')

