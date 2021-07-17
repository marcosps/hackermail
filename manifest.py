#!/usr/bin/env python3

import argparse

import _hkml

def set_argparser(parser):
    _hkml.set_manifest_option(parser)
    parser.add_argument('--keywords', metavar='<keyword>', nargs='+',
            help='print manifest entries having key with this keywords')

def pr_directory(directory, keywords, depth=0):
    indent = ' ' * 4 * depth
    for key in directory:
        found = False
        if keywords:
            for keyword in keywords:
                if key.find(keyword) != -1:
                    found = True
                    break
            if not found:
                continue

        val = directory[key]

        if type(val) == dict:
            print('%s%s: {' % (indent, key))
            pr_directory(val, None, depth + 1)
            print('%s}' % indent)
        else:
            print('%s%s: %s' % (indent, key, val))

def main(args=None):
    if not args:
        parser = argparse.ArgumentParser()
        set_argparser(parser)
        args = parser.parse_args()

    pr_directory(_hkml.get_manifest(args.manifest), args.keywords)

if __name__ == '__main__':
    main()
