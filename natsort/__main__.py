# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals, absolute_import

import sys
import os
import re

from .natsort import natsort_key, natsorted, int_nosign_re, int_sign_re
from .natsort import float_sign_exp_re, float_nosign_exp_re
from .natsort import float_sign_noexp_re, float_nosign_noexp_re
from .natsort import regex_and_num_function_chooser
from ._version import __version__
from .py23compat import py23_str


def main():
    """\
    Performs a natural sort on entries given on the command-line.
    A natural sort sorts numerically then alphabetically, and will sort
    by numbers in the middle of an entry.
    """

    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    from textwrap import dedent
    parser = ArgumentParser(description=dedent(main.__doc__),
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version',
                        version='%(prog)s {0}'.format(__version__))
    parser.add_argument('-f', '--filter', help='Used for '
                        'keeping only the entries that have a number '
                        'falling in the given range.', nargs=2, type=float,
                        metavar=('LOW', 'HIGH'), action='append')
    parser.add_argument('-e', '--exclude', type=float, action='append',
                        help='Used to exclude an entry '
                        'that contains a specific number.')
    parser.add_argument('-r', '--reverse', help='Returns in reversed order.',
                        action='store_true', default=False)
    parser.add_argument('-t', '--number-type', '--number_type', dest='number_type',
                         choices=('digit', 'int', 'float', 'version', 'ver'),
                         default='float', help='Choose the type of number '
                         'to search for. "float" will search for floating-point '
                         'numbers.  "int" will only search for integers. '
                         '"digit", "version", and "ver" are shortcuts for "int" '
                         'with --nosign.')
    parser.add_argument('--nosign', default=True, action='store_false',
                        dest='signed', help='Do not consider "+" or "-" as part '
                        'of a number, i.e. do not take sign into consideration.')
    parser.add_argument('--noexp', default=True, action='store_false',
                        dest='exp', help='Do not consider an exponential as part '
                        'of a number, i.e. 1e4, would be considered as 1, "e", '
                        'and 4, not as 10000.  This only effects the '
                        '--number_type=float.')
    parser.add_argument('entries', help='The entries to sort. Taken from stdin '
                        'if nothing is given on the command line.', nargs='*',
                        default=sys.stdin)
    args = parser.parse_args()

    # Make sure the filter range is given properly. Does nothing if no filter
    args.filter = check_filter(args.filter)

    # Remove trailing whitespace from all the entries
    entries = [e.strip() for e in args.entries]

    # Sort by directory then by file within directory and print.
    sort_and_print_entries(entries, args)


def range_check(low, high):
    """\
    Verifies that that given range has a low lower than the high.
    If the condition is not met, a ValueError is raised.
    Otherwise, the values are returned, but as floats.
    """
    low, high = float(low), float(high)
    if low >= high:
        raise ValueError('low >= high')
    else:
        return low, high


def check_filter(filt):
    """\
    Check that the low value of the filter is lower than the high.
    If there is to be no filter, return 'None'.
    If the condition is not met, a ValueError is raised.
    Otherwise, the values are returned, but as floats.
    """
    # Quick return if no filter.
    if not filt:
        return None
    try:
        return [range_check(f[0], f[1]) for f in filt]
    except ValueError as a:
        raise ValueError('Error in --filter: '+py23_str(a))


def keep_entry_range(entry, lows, highs, converter, regex):
    """\
    Boolean function to determine if an entry should be kept out
    based on if any numbers are in a given range.

    Returns True if it should be kept (i.e. falls in the range),
    and False if it is not in the range and should not be kept.
    """
    return any(low <= converter(num) <= high
                  for num in regex.findall(entry)
                  for low, high in zip(lows, highs))


def exclude_entry(entry, values, converter, regex):
    """\
    Boolean function to determine if an entry should be kept out
    based on if it contains a specific number.

    Returns True if it should be kept (i.e. does not match),
    and False if it matches and should not be kept.
    """
    return not any(converter(num) in values for num in regex.findall(entry))


def sort_and_print_entries(entries, args):
    """Sort the entries, applying the filters first if necessary."""

    # Extract the proper number type.
    kwargs = {'number_type': {'digit': None,
                              'version': None,
                              'ver': None,
                              'int': int,
                              'float': float}[args.number_type],
              'signed': args.signed,
              'exp': args.exp}

    # Pre-remove entries that don't pass the filtering criteria
    # Make sure we use the same searching algorithm for filtering as for sorting.
    if args.filter is not None or args.exclude:
        inp_options = (kwargs['number_type'], args.signed, args.exp)
        regex, num_function = regex_and_num_function_chooser[inp_options]
        if args.filter is not None:
            lows, highs = [f[0] for f in args.filter], [f[1] for f in args.filter]
            entries = [entry for entry in entries
                            if keep_entry_range(entry, lows, highs, num_function, regex)]
        if args.exclude:
            exclude = set(args.exclude)
            entries = [entry for entry in entries
                            if exclude_entry(entry, exclude, num_function, regex)]

    # Print off the sorted results
    entries.sort(key=lambda x: natsort_key(x, **kwargs), reverse=args.reverse)
    for entry in entries:
        print(entry)


if __name__ == '__main__':
    try:
        main()
    except ValueError as a:
        sys.exit(py23_str(a))
    except KeyboardInterrupt:
        sys.exit(1)
