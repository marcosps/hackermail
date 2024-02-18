# SPDX-License-Identifier: GPL-2.0

import argparse
import datetime
import json
import os
import time

import _hkml

# Cache is constructed with multiple files.
# active cache: Contains most recently added cache entries.
# archieved cache: Contains cache entries that added older than oldest one in
# the active cache.
#
# Size of cache files are limited to about 100 MiB.
# Up to 9 archived cache files can exist.
# When the size of active cache becomes >=100 MiB, delete oldest archived
# cache, make the active cache a newest archived cache, and create a new active
# cache.
#
# When reading the cache, active cache is first read, then archived caches one by
# one, recent archive first, until the item is found.

def load_cache_config():
    cache_config_path = os.path.join(_hkml.get_hkml_dir(),
                                     'mails_cache_config')
    if not os.path.isfile(cache_config_path):
        return {'max_active_cache_sz': 100 * 1024 * 1024,
                'max_archived_caches': 9}

    with open(cache_config_path, 'r') as f:
        return json.load(f)

# dict having gitid/gitdir as key, Mail kvpairs as value

archived_caches = []
active_cache = None
total_cache = {}

mails_cache = None
need_file_update = False

def get_cache_key(gitid=None, gitdir=None, msgid=None):
    if gitid is not None:
        return '%s/%s' % (gitid, gitdir)
    return msgid

def list_archive_files():
    """Return a list of archived cache files sorted in recent one first"""
    archive_files = []
    for file_ in os.listdir(_hkml.get_hkml_dir()):
        if file_.startswith('mails_cache_archive_'):
            archive_files.append(
                    os.path.join(_hkml.get_hkml_dir(), file_))
    # name is mails_cache_archive_<timestamp>
    archive_files.sort(reverse=True)
    return archive_files

def get_active_mails_cache():
    global active_cache

    if active_cache is not None:
        return active_cache

    active_cache = {}
    cache_path = os.path.join(_hkml.get_hkml_dir(), 'mails_cache_active')
    if os.path.isfile(cache_path):
        stat = os.stat(cache_path)
        if stat.st_size >= load_cache_config()['max_active_cache_sz']:
            os.rename(
                    cache_path, os.path.join(
                        _hkml.get_hkml_dir(), 'mails_cache_archive_%s' %
                        datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')))
            archive_files = list_archive_files()
            if len(archive_files) > load_cache_config()['max_archived_caches']:
                os.remove(archive_files[-1])
        else:
            with open(cache_path, 'r') as f:
                active_cache = json.load(f)
    return active_cache

def load_one_more_archived_cache():
    global archived_caches

    archive_files = list_archive_files()
    if len(archive_files) == len(archived_caches):
        return False
    with open(archive_files[len(archived_caches)], 'r') as f:
        archived_caches.append(json.load(f))
    return True

def get_mail(gitid=None, gitdir=None, key=None):
    global archived_caches

    if key is None:
        key = get_cache_key(gitid, gitdir)

    cache = get_active_mails_cache()
    if key in cache:
        return _hkml.Mail(kvpairs=cache[key])
    for cache in archived_caches:
        if key in cache:
            return _hkml.Mail(kvpairs=cache[key])
    while load_one_more_archived_cache() == True:
        if key in archived_caches[-1]:
            return _hkml.Mail(kvpairs=archived_caches[-1][key])
    return None

def set_mail(mail):
    global need_file_update

    if mail.broken():
        return

    cache = get_active_mails_cache()
    if mail.gitid is not None and mail.gitdir is not None:
        key = get_cache_key(mail.gitid, mail.gitdir)
    else:
        key = mail.get_field('message-id')
    if key in cache:
        return
    for archived_cache in archived_caches:
        if key in archived_cache:
            return
    cache[key] = mail.to_kvpairs()
    need_file_update = True

def writeback_mails():
    if not need_file_update:
        return
    cache_path = os.path.join(_hkml.get_hkml_dir(), 'mails_cache_active')
    with open(cache_path, 'w') as f:
        json.dump(get_active_mails_cache(), f, indent=4)

def pr_cache_stat(cache_path):
    print('Stat of %s' % cache_path)
    cache_stat = os.stat(cache_path)
    print('cache size: %.3f MiB' % (cache_stat.st_size / 1024 / 1024))

    before_timestamp = time.time()
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    print('%d mails in cache' % len(cache))
    print('%f seconds for json-loading cache' %
          (time.time() - before_timestamp))

    before_timestamp = time.time()
    for key in cache:
        mail = _hkml.Mail(kvpairs=cache[key])
    print('%f seconds for parsing mails' % (time.time() - before_timestamp))

def show_cache_status(config_only):
    cache_config = load_cache_config()
    print('max active cache file size: %s bytes' %
          cache_config['max_active_cache_sz'])
    print('max archived caches: %d' % cache_config['max_archived_caches'])
    if config_only is True:
        return
    print()

    cache_path = os.path.join(_hkml.get_hkml_dir(), 'mails_cache_active')
    if not os.path.isfile(cache_path):
        print('no cache exist')
        exit(1)

    pr_cache_stat(cache_path)
    print('')
    for archived_cache in list_archive_files():
        pr_cache_stat(archived_cache)
        print('')

def main(args):
    if args.action == 'status':
        show_cache_status(args.config_only)

def set_argparser(parser):
    parser.description = 'manage mails cache'

    subparsers = parser.add_subparsers(
            title='action', dest='action', metavar='<action>')

    parser_status = subparsers.add_parser('status', help='show cache status')
    parser_status.add_argument('--config_only', action='store_true',
                               help='show configuration status only')
