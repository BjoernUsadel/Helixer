#! /usr/bin/env python3
import argparse
from pprint import pprint

from helixer.export.exporter import HelixerExportController, HelixerFastaToH5Controller
from geenuff2h5 import export_parser_base, io_group, check_export_args


if __name__ == '__main__':
    io_group.add_argument('--fasta-path', type=str, default=None,
                          help='Directly convert from a FASTA file to .h5')
    io_group.add_argument('--species', type=str, default='', help='Species name.')

    args = export_parser_base.parse_args()
    check_export_args(args)
    controller = HelixerFastaToH5Controller(args.fasta_path, args.output_path)
    controller.export_fasta_to_h5(chunk_size=args.chunk_size, compression=args.compression,
                                  multiprocess=not args.no_multiprocess, species=args.species)

