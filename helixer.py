#! /usr/bin/env python3
import os
import yaml
import argparse
from pprint import pprint
from geenuff2h5 import export_parser_base, get_and_check_args, io_group, data_group


if __name__ == '__main__':
    io_group.add_argument('--config-path', type=str, default='config/helixer_config.yaml',
                          help='Config in form of a YAML file with lower priority than parameters given on the command line.')
    io_group.add_argument('--fasta-path', type=str, default=None,
                          help='Directly convert from a FASTA file to .h5')
    io_group.add_argument('--species', type=str, default='', help='Species name.')
    data_group.add_argument('--species-category', type=str, default='vertebrate', choices=['vertebrate', 'land_plant', 'fungi'],
                            help='What model to use for the annotation. (Default is "vertebrate".)'

    post_group = export_parser_base.add_argument_group("Post processing parameters")
    post_group.add_argument('--window-size', type=int, default=100, help='')
    post_group.add_argument('--edge-threshold', type=float, default=0.1, help='')
    post_group.add_argument('--peak-threshold', type=float, default=0.8, help='')
    post_group.add_argument('--min-coding-length', type=int, default=100, help='')
    args = get_and_check_args(export_parser_base)

    controller = HelixerFastaToH5Controller(args.fasta_path, args.output_path)
    controller.export_fasta_to_h5(chunk_size=args.chunk_size, compression=args.compression,
                                  multiprocess=not args.no_multiprocess, species=args.species)

