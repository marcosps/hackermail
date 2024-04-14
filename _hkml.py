#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import base64
import datetime
import email.utils
import json
import mailbox
import os
import subprocess
import time
import sys

import hkml_cache
import hkml_list

def cmd_str_output(cmd):
    output = subprocess.check_output(cmd)
    try:
        return output.decode('utf-8').strip()
    except UnicodeDecodeError as e:
        return output.decode('cp437').strip()

def cmd_lines_output(cmd):
    return cmd_str_output(cmd).split('\n')

def atom_tag(node):
    prefix = '{http://www.w3.org/2005/Atom}'
    if not node.tag.startswith(prefix):
        return node.tag
    return node.tag[len(prefix):]

class Mail:
    gitid = None
    gitdir = None
    subject = None
    date = None
    subject_tags = None
    series = None
    __fields = None
    mbox = None
    replies = None
    parent_mail = None

    def set_subject_tags_series(self):
        subject = self.subject
        tag_start_idx = subject.find('[')
        if tag_start_idx != 0:
            return

        tag_end_idx = subject.find(']')
        if tag_end_idx == -1:
            return

        tag = subject[tag_start_idx + 1: tag_end_idx].strip().lower()
        self.subject_tags += tag.split()

        series = self.subject_tags[-1].split('/')
        if (len(series) == 2 and series[0].isdigit() and
                series[1].isdigit()):
            self.series = [int(x) for x in series]

    @classmethod
    def from_gitlog(cls, gitid, gitdir, date, subject):
        mail = hkml_cache.get_mail(gitid, gitdir)
        if mail != None:
            return mail
        self = cls()
        self.gitid = gitid
        self.gitdir = gitdir
        try:
            self.date = datetime.datetime.fromisoformat(date).astimezone()
        except:
            # maybe lower version of python.
            # the input 'date' may have UTC offset with hour separator, like
            # '+05:00', while strptime() '%z' expoects no such separator.  Make
            # it compatible.
            date = '%s%s' % (date[:-3], date[-2:])
            self.date = datetime.datetime.strptime(
                    date, '%Y-%m-%dT%H:%M:%S%z').astimezone()
        self.subject = subject
        self.set_subject_tags_series()
        self.__fields = {}
        hkml_cache.set_mail(self)
        return self

    def parse_atom(self, entry, mailing_list):
        self.__fields = {}
        pi_url = get_manifest()['site']
        http_prefix_len = len('%s/%s/' % (pi_url, mailing_list)) - 1
        for node in entry:
            tagname = atom_tag(node)
            if tagname == 'author':
                for child in node:
                    name = ''
                    email = ''
                    if atom_tag(child) == 'name':
                        name = child.text
                    elif atom_tag(child) == 'email':
                        email = child.text
                self.__fields['from'] = ' '.join([name, email])
            elif tagname == 'title':
                self.subject = node.text
            elif tagname == 'updated':
                self.date = datetime.datetime.strptime(
                        node.text, '%Y-%m-%dT%H:%M:%S%z').astimezone()
            elif tagname == 'link':
                link = node.attrib['href']
                msgid = link[http_prefix_len:-1]
                self.__fields['message-id'] = '<%s>' % msgid
            elif tagname.endswith('}in-reply-to'):
                link = node.attrib['href']
                self.__fields['in-reply-to'] = link[http_prefix_len:-1]
        if not 'in-reply-to' in self.__fields:
            self.__fields['in-reply-to'] = None

    def __init__(self, mbox=None, kvpairs=None, atom_entry=None, atom_ml=None):
        self.replies = []
        self.subject_tags = []

        if mbox is None and kvpairs is None and atom_entry is None:
            return

        if mbox is not None:
            self.mbox = mbox
        elif kvpairs is not None:
            self.gitid = kvpairs['gitid']
            self.gitdir = kvpairs['gitdir']
            self.subject = kvpairs['subject']
            self.mbox = kvpairs['mbox']
            if 'msgid' in kvpairs:
                self.__fields = {'message-id': kvpairs['msgid']}
        elif atom_entry is not None:
            self.parse_atom(atom_entry, atom_ml)
            hkml_cache.set_mail(self, overwrite=True)
            return

        self.__parse_mbox()
        date_str = self.get_field('date')
        if date_str == None:
            self.date = None
            return
        self.date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(
                    email.utils.parsedate_tz(date_str))).astimezone()
        self.subject = self.get_field('subject')
        if self.subject == None:
            return
        self.set_subject_tags_series()
        hkml_cache.set_mail(self)

    def broken(self):
        return self.date is None or self.subject is None

    def to_kvpairs(self):
        if self.mbox == None:
            # ensure mbox is set.  TODO: don't parse it unnecessarily
            self.get_field('message-id')
        return {
                'gitid': self.gitid,
                'gitdir': self.gitdir,
                'subject': self.subject,
                'msgid': self.__fields['message-id'],
                'mbox': self.mbox}

    def get_field(self, tag):
        tag = tag.lower()
        # this might set from git log
        if tag == 'subject' and self.subject:
            return self.subject

        if not tag in self.__fields:
            self.__parse_mbox()

        if not tag in self.__fields:
            return None
        return self.__fields[tag]

    def set_mbox(self):
        if self.gitdir is not None and self.gitid is not None:
            cmd = ['git', '--git-dir=%s' % self.gitdir,
                    'show', '%s:m' % self.gitid]
            try:
                self.mbox = cmd_str_output(cmd)
            except:
                self.mbox = ''
            return
        if 'message-id' in self.__fields:
            msgid = self.__fields['message-id']
            pi_url = get_manifest()['site']
            # mail.msgid is having '<' and '>' pre/suffix
            mbox_url = '%s/all/%s/raw' % (pi_url, msgid[1:-1])
            # don't overload the public inbox server
            time.sleep(0.3)
            try:
                self.mbox = subprocess.check_output(
                        ['curl', mbox_url], stderr=subprocess.DEVNULL).decode()
            except:
                print('cannot get mbox from public-inbox server')
                self.mbox = ''
            return
        print('cannot get mbox')
        exit(1)

    def __parse_mbox(self):
        if not self.mbox:
            self.set_mbox()

        in_header = True
        parsed = {}
        mbox_lines = self.mbox.split('\n')
        for idx, line in enumerate(mbox_lines):
            if in_header:
                if line and line[0] in [' ', '\t'] and key:
                    parsed[key] += ' %s' % line.strip()
                    continue
                line = line.strip()
                key = line.split(':')[0].lower()
                if key:
                    val = line[len(key) + 2:]
                    if key == 'message-id':
                        if len(val.split()) >= 1:
                            val = val.split()[0]
                    parsed[key] = val
                elif line == '':
                    in_header = False
                continue
            break
        try:
            # 'm' doesn't have start 'From' line in some case.  Add a fake one.
            mbox_str = '\n'.join(['From mboxrd@z Thu Jan  1 00:00:00 1970',
                self.mbox])
            parsed['body'] = mailbox.Message(
                    mbox_str).get_payload(decode=True).decode()
        except:
            # Still decode() could fail due to encoding
            parsed['body'] = '\n'.join(mbox_lines[idx:])

            encoding_key = 'Content-Transfer-Encoding'.lower()
            if encoding_key in parsed and parsed[encoding_key] == 'base64':
                try:
                    parsed['body'] = base64.b64decode(parsed['body']).decode()
                except:
                    pass

        # for lore-pasted string case
        if 'date' in parsed:
            tokens = parsed['date'].split()
            if tokens[-2:] == ['[thread', 'overview]']:
                parsed['date'] = ' '.join(tokens[:-2])

        self.__fields = parsed

    def add_tag(self, tag):
        body = self.get_field('body')
        if body is None:
            return 'getting body text failed'
        lines = body.split('\n')
        for idx, line in enumerate(lines):
            if line != '---':
                continue
            lines.insert(idx, tag)
            self.__fields['body'] = '\n'.join(lines)
            return None
        return 'cannot find line to add the tag'

    def add_cv(self, cvmail, sz_patchset):
        new_body_lines = []

        cv_subject = cvmail.get_field('subject')
        first_paragraph = hkml_list.wrap_line(
                'Patch series', '\'%s\'' % cv_subject, 72)
        first_paragraph = '\n'.join(first_paragraph)
        new_body_lines.append(first_paragraph)
        new_body_lines.append('')

        cv_paragraphs = cvmail.get_field('body').strip().split('\n\n')
        cv_msg = '\n\n'.join(cv_paragraphs[:-3])
        new_body_lines.append(cv_msg)

        new_body_lines += ['', 'This patch (of %d):' % sz_patchset, '']
        new_body_lines.append(self.get_field('body'))
        new_body = '\n'.join(new_body_lines)
        self.__fields['body'] = new_body

def read_mbox_file(filepath):
    mails = []
    if filepath[-5:] == '.json':
        with open(filepath, 'r') as f:
            for kvp in json.load(f):
                mail = Mail(kvpairs=kvp)
                if mail.broken():
                    continue
                mails.append(mail)
            return mails

    for message in mailbox.mbox(filepath):
        mail = Mail(mbox='%s' % message)
        if mail.broken():
            continue
        mails.append(mail)
    return mails

def read_mails_from_clipboard():
    mbox_str = cmd_str_output(['xclip', '-o', '-sel', 'clip'])
    mail = Mail(mbox=mbox_str)
    if mail.broken():
        return [], 'clipboard is not complete mbox string'
    return [mail], None

__hkml_dir = None
__manifest = None

def set_hkml_dir(path=None):
    global __hkml_dir
    if path:
        if not os.path.exists(path):
            sys.stderr.write('Given hkml_dir %s does not exists\n' % path)
            exit(1)
        __hkml_dir = path
        return

    THE_DIR='.hkm'
    env_dir = os.getenv('HKML_DIR')
    if env_dir and os.path.exists(env_dir):
        __hkml_dir = env_dir
    cwd_dir = os.path.join(os.getcwd(), THE_DIR)
    if cwd_dir and os.path.exists(cwd_dir):
        __hkml_dir = cwd_dir
    bin_dir = os.path.join(os.path.dirname(sys.argv[0]), THE_DIR)
    if bin_dir and os.path.exists(bin_dir):
        __hkml_dir = bin_dir
    home_dir = os.path.join(os.getenv('HOME'), THE_DIR)
    if home_dir and os.path.exists(home_dir):
        __hkml_dir = home_dir
    if not __hkml_dir:
        sys.stderr.write('hkml metadata directory is not found from\n')
        sys.stderr.write('    \'$HKML_DIR\' (%s),\n' % env_dir)
        sys.stderr.write('    current directory (%s),\n' % cwd_dir)
        sys.stderr.write('    \'hkml\' binary directory (%s), and\n' % cwd_dir)
        sys.stderr.write('    your home directory (%s)\n' % cwd_dir)
        sys.stderr.write('have you forgot running \'hkml init\'?\n')
        exit(1)

def get_hkml_dir():
    if not __hkml_dir:
        set_hkml_dir()
    return __hkml_dir

def set_hkml_dir_manifest(hkml_dir, manifest):
    global __manifest

    set_hkml_dir(hkml_dir)
    if manifest is None:
        manifest = os.path.join(get_hkml_dir(), 'manifest')

    try:
        with open(manifest, 'r') as f:
            __manifest = json.load(f)
    except:
        sys.stderr.write('Manifest (%s) load failed\n' % manifest)
        exit(1)

def get_manifest():
    if __manifest is None:
        sys.stderr.write('BUG: Manifest file is not set\n')
        exit(1)
    return __manifest

def __get_epoch_from_git_path(git_path):
    # git_path is, e.g., '.../0.git'
    return int(os.path.basename(git_path).split('.git')[0])

def mail_list_repo_paths(mail_list, manifest=None):
    '''Returns git trees in the manifest for the given mailing lists.

    Note that the paths are sorted by the epochs of the git trees in
    descsending order.'''

    if manifest is None:
        manifest = get_manifest()

    paths = []
    for path in manifest:
        if path.startswith('/%s/' % mail_list):
            paths.append(path)
    return sorted(paths, key=__get_epoch_from_git_path, reverse=True)

def mail_list_data_paths(mail_list, manifest=None):
    '''Returns git trees in this machine for the given mailing lists.

    Note that the paths are sorted by the epochs of the git trees in
    descsending order.'''

    if manifest is None:
        manifest = get_manifest()

    repo_paths = mail_list_repo_paths(mail_list, manifest)
    mdir_paths = []
    for path in repo_paths:
        mdir_paths.append(os.path.join(get_hkml_dir(), 'archives' + path))
    return sorted(mdir_paths, key=__get_epoch_from_git_path, reverse=True)

def is_valid_mail_list(name):
    for mail_list_git_path in get_manifest().keys():
        if mail_list_git_path.startswith('/%s/' % name):
            return True
    return False

def set_manifest_option(parser):
    parser.add_argument('--manifest', metavar='<file>', type=str,
            help='Manifesto file in grok\'s format plus site field.')
