# SPDX-License-Identifier: GPL-2.0

import _hkml

class HkmlMonitorRequest:
    mailing_lists = None
    sender_keywords = None
    subject_keywords = None
    body_keywords = None
    thread_of = None

    notify_send_mail = None
    notify_write_file = None
    notify_frequency = None

def set_argparser(parser):
    _hkml.set_manifest_option(parser)
    subparsers = parser.add_subparsers(
            title='action', dest='action', metavar='<action>')

    parser_add = subparsers.add_parser('add', help='add a monitoring request')
    parser_add.add_argument('foo')

    parser_remove = subparsers.add_parser(
            'remove', help='remove a given monitoring request')

    parser_status = subparsers.add_parser(
            'status', help='show monitoring status including requests')

    parser_start = subparsers.add_parser(
            'start', help='start monitoring')

    parser_stop = subparsers.add_parser(
            'stop', help='stop monitoring')

def main(args):
    if args.action == 'add':
        print('add monitor query')
    elif args.action == 'remove':
        print('remove monitor query')
