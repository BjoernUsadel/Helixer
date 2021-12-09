#! /usr/bin/env python3
import argparse
from pprint import pprint

from helixer.export.exporter import HelixerExportController, HelixerFastaToH5Controller
from geenuff2h5 import export_parser_base, get_and_check_args, io_group, data_group


if __name__ == '__main__':
    io_group.add_argument('--config-path', type=str, default='config/fasta2h5_config.yaml',
                          help='Config in form of a YAML file with lower priority than parameters given on the command line.')
    io_group.add_argument('--fasta-path', type=str, default=None, required=True
                          help='Directly convert from a FASTA file to .h5')
    io_group.add_argument('--species', type=str, default='', help='Species name.')
    data_group.add_argument('--chunk-size', type=int, default=20000,
                            help='Size of the chunks each genomic sequence gets cut into. (Default is 20000)')
    args = get_and_check_args(export_parser_base)

    controller = HelixerFastaToH5Controller(args.fasta_path, args.output_path)
    controller.export_fasta_to_h5(chunk_size=args.chunk_size, compression=args.compression,
                                  multiprocess=not args.no_multiprocess, species=args.species)

