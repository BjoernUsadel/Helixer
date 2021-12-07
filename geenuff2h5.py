#! /usr/bin/env python3
import os
import argparse
from pprint import pprint

from helixer.export.exporter import HelixerExportController, HelixerFastaToH5Controller


# set this aside so it can be imported by fasta2h5.py
export_parser_base = argparse.ArgumentParser()
io_group = export_parser_base.add_argument_group("Data input and output")
io_group.add_argument('--output-path', type=str, required=True,
                      help='Output file for the encoded data. Must end with ".h5"')

data_group = export_parser_base.add_argument_group("Data generation parameters")
data_group.add_argument('--chunk-size', type=int, default=20000,
                        help='Size of the chunks each genomic sequence gets cut into. (Default is 20000)')
data_group.add_argument('--compression', type=str, default='gzip', choices=['gzip', 'lzf'],
                        help='Compression algorithm used for the intermediate .h5 output files with a fixed compression '
                             'level of 4. (Default is "gzip", which is much slower than "lzf".)')
data_group.add_argument('--no-multiprocess', action='store_true',
                        help='Whether to not parallize the numerification of large sequences. Uses half the memory '
                             'but can be much slower when many CPU cores can be utilized.')


def check_export_args(args):
    assert args.output_path.endswith('.h5'), '--output-path must end with ".h5"'
    print('{os.path.basename(__file__)} export config:')
    pprint(vars(args))
    print()


def main(args):
    if args.modes == 'all':
        modes = ('X', 'y', 'anno_meta', 'transitions')
    else:
        modes = tuple(args.modes.split(','))

    if args.add_additional:
        match_existing = True
        h5_group = '/alternative/' + args.add_additional + '/'
    else:
        match_existing = False
        h5_group = '/data/'

    write_by = round(args.write_by / args.chunk_size) * args.chunk_size
    controller = HelixerExportController(args.input_db_path, args.output_path, match_existing=match_existing,
                                         h5_group=h5_group)
    controller.export(chunk_size=args.chunk_size, write_by=write_by, modes=modes, compression=args.compression,
                      multiprocess=not args.no_multiprocess)


if __name__ == '__main__':
    io_group.add_argument('--input-db-path', type=str, default=None,
                          help='Path to the GeenuFF SQLite input database (has to contain only one genome).')
    io_group.add_argument('--add-additional', type=str, default='',
                          help='Outputs the datasets under alternatives/{add-additional}/ (and checks sort order against '
                               'existing "data" datasets). Use to add e.g. additional annotations from Augustus.')
    data_group.add_argument('--modes', default='all',
                            help='Either "all" (default), or a comma separated list with desired members of the following '
                                 '{X, y, anno_meta, transitions} that should be exported. This can be useful, for '
                                 'instance when skipping transitions (to reduce size/mem) or skipping X because '
                                 'you are adding an additional annotation set to an existing file.')
    data_group.add_argument('--write-by', type=int, default=10_000_000_000,
                            help='Write in super-chunks with this many base pairs, which will be rounded to be '
                                 'divisible by chunk-size. (Default is 10_000_000_000).')
    args = export_parser_base.parse_args()
    check_export_args(args)
    main(args)
