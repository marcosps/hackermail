#!/usr/bin/env python3

import argparse
import fetchmails
import lsmails
import format_reply
import os
import subprocess
import sys
import tempfile

class SubCmdHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        parts = super(argparse.RawDescriptionHelpFormatter,
                self)._format_action(action)
        # Skips subparsers help
        if action.nargs == argparse.PARSER:
            parts = '\n'.join(parts.split('\n')[1:])
        return parts

parser = argparse.ArgumentParser(formatter_class=SubCmdHelpFormatter)
subparsers = parser.add_subparsers(title='command', dest='command',
        metavar='<command>')

parser_ls = subparsers.add_parser('ls', help = 'list mails')
lsmails.set_argparser(parser_ls)

parser_fetch = subparsers.add_parser('fetch', help = 'fetch mails')
fetchmails.set_argparser(parser_fetch)

parser_fmtre = subparsers.add_parser('format-reply', help = 'format reply')
format_reply.set_argparser(parser_fmtre)

args = parser.parse_args()

if not args.command:
    parser.print_help()
    exit(1)

if args.command == 'ls':
    tmp_path = tempfile.mkstemp()[1]
    with open(tmp_path, 'w') as tmp_file:
        sys.stdout = tmp_file

        lsmails.main(args)

        tmp_file.flush()
        subprocess.call(['less', tmp_path])
    os.remove(tmp_path)
elif args.command == 'fetch':
    fetchmails.main(args)
elif args.command == 'format-reply':
    format_reply.main(args)
