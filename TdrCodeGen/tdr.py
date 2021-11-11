#!/usr/bin/env python
# ecoding: utf-8

import sys
import os
import logging
import argparse

VERSION = '2.7.37'

def _add_lib_path():
    mydir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.join(mydir, 'lib'))

def main():
    """
    ex: python tdr.py -c python test.xml
    """
    class KVAppendAction(argparse.Action):
        """
        key-value parser
        """
        def __call__(self, parser, args, values, option_string=None):
            assert(len(values) == 1)
            try:
                k, v = values[0].split("=", 2)
            except ValueError as _:
                raise argparse.ArgumentError(self, "could not parse argument \"{values[0]}\" as k=v format")
            d = getattr(args, self.dest) or {}
            d[k] = v
            setattr(args, self.dest, d)

    parser = argparse.ArgumentParser(description="Current tdr.py version %s" % (VERSION))
    parser.add_argument("xml", nargs="+", default=[])
    parser.add_argument("-I", "--include", nargs="+", help="search path for meta file included", default=[])
    parser.add_argument("-O", "--output", help="output directory, default is current directory", default="")
    parser.add_argument("-C", "--compiler", help="compiler name, default is python; python, go ...", default="go")
    parser.add_argument("-D", "--debug", help="debug output", action="store_true", default=False)
    parser.add_argument("-P", "--params", 
                        nargs=1,
                        action=KVAppendAction,
                        metavar="KEY=VALUE",
                        help="KEY=VALUE: add compiler params",
                        default={})
    args = parser.parse_args()

    log_lv = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=log_lv, format='%(message)s')
    _add_lib_path()
    import core

    c = core.setup_compiler(args.compiler, VERSION, args.output, args.params)
    for f in args.xml:
        m = core.Metalib(f, c, [os.path.dirname(f)] + args.include)
        m.compile()
    c.complete()


if __name__ == '__main__':
    main()
