#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import subprocess
import tempfile

import _hkml
import hkml_cache
import hkml_list
import hkml_open

def set_argparser(parser=None):
    parser.description='list mails of a thread'
    _hkml.set_manifest_option(parser)
    parser.add_argument(
            'mail_idx', metavar='<mail index>', type=int,
            help='index of any mail in the thread to list')
    parser.add_argument('--lore', action='store_true',
            help='print lore link for mails')
    parser.add_argument(
            '--dont_use_b4', action='store_true',
            help='don\'t use b4 but only previous list\'s output')

def get_thread_mails_use_b4(msgid):
    fd, tmp_path = tempfile.mkstemp(prefix='hkml_thread_')
    if subprocess.call(['b4', 'mbox', '--mbox-name', tmp_path, msgid],
                       stderr=subprocess.DEVNULL) != 0:
        return None, 'b4 mbox failed'
    mails = hkml_list.get_mails(
            tmp_path, False, None, None, None, None, None)
    os.remove(tmp_path)
    return mails, None

def main(args=None):
    if not args:
        parser = argparse.ArgumentParser()
        set_argparser(parser)
        args = parser.parse_args()

    if subprocess.call(['which', 'b4'], stdout=subprocess.DEVNULL) == 0:
        use_b4 = args.dont_use_b4 is False

    if use_b4:
        mail = hkml_list.get_mail(args.mail_idx, no_thread_output=True)
        if mail is None:
            print('wrong <mail_idx>')
            exit(1)
        msgid = mail.get_field('message-id')

        mails_to_show, err = get_thread_mails_use_b4(msgid)
        if err is not None:
            print(err)
            exit(1)

        args.mail_idx = None
    else:
        mails_to_show = hkml_list.last_listed_mails()

    nr_cols_in_line = int(os.get_terminal_size().columns * 9 / 10)
    to_show = hkml_list.mails_to_str(
            mails_to_show, mails_filter=None, show_stat=False,
            show_thread_of=args.mail_idx, descend=False,
            sort_threads_by=['first_date'], collapse_threads=None,
            open_mail_via_lore=False,
            show_lore_link=args.lore, nr_cols=nr_cols_in_line,
            runtime_profile=[], show_runtime_profile=False)

    if use_b4:
        hkml_cache.writeback_mails()
        hkml_list.cache_list_output('thread_output', to_show)
    hkml_open.pr_with_pager_if_needed(to_show)

if __name__ == '__main__':
    main()
