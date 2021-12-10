#! /usr/bin/env python3
import os
import yaml
import argparse
from pprint import pprint

from helixer.export.exporter import HelixerExportController, HelixerFastaToH5Controller


class ParameterParser(object):
    """Bundles code that parses script parameters from the command line and a config file."""

    def __init__(self, config_file_path=''):
        # Do NOT use default values in the argparse configuration but specify them seperately later
        # (except for the config file itself)
        # This is needed to give the cli parameters precedent over the ones in the config file
        self.parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
        self.io_group = self.parser.add_argument_group("Data input and output")
        self.io_group.add_argument('--config-path', type=str, default=config_file_path,
                              help='Config in form of a YAML file with lower priority than parameters given on the command line.')

        self.data_group = self.parser.add_argument_group("Data generation parameters")
        self.data_group.add_argument('--compression', type=str, choices=['gzip', 'lzf'],
                                     help='Compression algorithm used for the intermediate .h5 output '
                                          'files with a fixed compression level of 4. '
                                          '(Default is "gzip", which is much slower than "lzf".)')
        self.data_group.add_argument('--no-multiprocess', action='store_true',
                                     help='Whether to not parallize the numerification of large sequences. Uses half the memory '
                                          'but can be much slower when many CPU cores can be utilized.')

        # Default values have to be specified - and potentially added - here
        self.defaults = {'compression': 'gzip', 'no_multiprocess': False}

    @staticmethod
    def check_args(args):
        pass

    def load_and_merge_parameters(self, args):
        config = {}
        if args.config_path and os.path.isfile(args.config_path):
            with open(args.config_path, 'r') as f:
                try:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        # an empty yaml file will result in a None object
                        config = yaml_config
                except yaml.YAMLError as e:
                    print(f'An error occured during parsing of the YAML config file: {e} '
                          '\nNot using the config file.')
        else:
            print(f'No config file found\n')

        # merge the config and cli parameters with the cli parameters having priority
        # there are no type checks being done for config parameters
        config = {**self.defaults, **config, **vars(args)}
        return argparse.Namespace(**config)

    def get_args(self):
        args = self.parser.parse_args()
        args = self.load_and_merge_parameters(args)
        ParameterParser.check_args(args)

        print(f'{os.path.basename(__file__)} export config:')
        pprint(vars(args))
        print()
        return args


class ExportParameterParser(ParameterParser):
    def __init__(self, config_file_path=''):
        self.io_group.add_argument('--h5-output-path', type=str, required=True,
                                   help='HDF5 output file for the encoded data. Must end with ".h5"')

    @staticmethod
    def check_args(args):
        assert args.h5_output_path.endswith('.h5'), '--output-path must end with ".h5"'


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
    controller = HelixerExportController(args.input_db_path, args.h5_output_path, match_existing=match_existing,
                                         h5_group=h5_group)
    controller.export(chunk_size=args.chunk_size, write_by=write_by, modes=modes, compression=args.compression,
                      multiprocess=not args.no_multiprocess)


if __name__ == '__main__':
    pp = ExportParameterParser(config_file_path='config/geenuff2h5_config.yaml')

    pp.io_group.add_argument('--input-db-path', type=str, required=True,
                            help='Path to the GeenuFF SQLite input database (has to contain only one genome).')
    pp.io_group.add_argument('--add-additional', type=str,
                            help='Outputs the datasets under alternatives/{add-additional}/ (and checks sort order against '
                                 'existing "data" datasets). Use to add e.g. additional annotations from Augustus.')
    pp.data_group.add_argument('--chunk-size', type=int,
                              help='Size of the chunks each genomic sequence gets cut into. (Default is 20000)')
    pp.data_group.add_argument('--modes', type=str,
                              help='Either "all" (default), or a comma separated list with desired members of the following '
                                   '{X, y, anno_meta, transitions} that should be exported. This can be useful, for '
                                   'instance when skipping transitions (to reduce size/mem) or skipping X because '
                                   'you are adding an additional annotation set to an existing file.')
    pp.data_group.add_argument('--write-by', type=int,
                              help='Write in super-chunks with this many base pairs, which will be rounded to be '
                                   'divisible by chunk-size. (Default is 10_000_000_000).')

    # need to add any default values like this
    pp.defaults['add_additional'] = ''
    pp.defaults['chunk_size'] = 20000
    pp.defaults['modes'] = 'all'
    pp.defaults['write_by'] = 10_000_000_000

    args = pp.get_args()
    main(args)
