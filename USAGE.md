This document describes the detailed usage of `hkml`.  This doesn't cover all
details of `hkml` but only major features.  This document may not complete and
up to date sometimes.  Please don't hesitate at asking questions or help for
this document via GitHub issues.

Demo
====

[![asciicast](https://asciinema.org/a/632442.svg)](https://asciinema.org/a/632442)

Commands
========

Hackermail can be executed using `hkml` command.  Using sub-command of it,
users can manipulate mails.  Users can show the list of sub-commands via the
`--help` option of `hkml`.  Similarly, each subcommand support `--help` option.

Initialization
==============

To properly work, hackermail requires 1) working directory, and 2) mailing
lists manifest.

Working Directory
-----------------

Working directory is a directory to save the fetched mails and hanckermail's
metadata.  You may think this as something similar to `.git` directory of git.

You can explicitly set the path to the directory using `HKML_DIR` environment
variable, or `--hkml_dir` option of each sub-command.  If the path is not
specified, hackermail assumes the directory is named as `.hkm` and placed under
current directory, the `hkml` executable file placed directory, or your home
directory and try to find it.  If it cannot find a proper working directory,
most of `hkml` sub-command will fail.

Manifest File
-------------

Manifest file is a file for information on mailing lists that you want to
communicate with using `hkml`.  It describes from where in the internet the
mails you want to read can be fetched, name of the mailing lists archived in
the site, and the site-relative path to the git repositories for each mailing
list in json format.  It's very similar to that of lore[1] except the fact that
hackermail manifest is containing the site information.  A sample manifest file
for the linux kernel mailing lists is located at `manifests/lore.js`, which has
generated by `update_lore_manifest.sh`.

You can explicitly set the path to the manifest file using `--manifest` option
of each sub-command.  If it is not specified, hackermail assumes it is placed
under the working directory in name of `manifest` and try to use it.

[1] https://www.kernel.org/lore.html

`init` sub-command
------------------

`init` sub-command of `hkml` does setting the working directory and manifest
file.  For example, if you call below command on this directory, it will create
the working directory as `.hkm` directory under the repo, and Linux kernel
mailing list as the manifest.  Hence, you will be able to use `hkml` for Linux
kernel mails from anywhere by using `hkml` file in this directory.

```
$ hkml init --manifest ./manifests/lore.json
```

Fetching Mails
==============

Users can download mails from specific mailing list that described on the
manifest file onto the local storage using `fetch` sub-command.  It receives
the names of the mailing lists to fetch.  By default, it receives latest
epoch's mails of given mailing lists.  For example, below command downloads
recent mails from linux-mm mailing list.

```
$ hkml fetch linux-mm
```

Note that fetching can be done with `list` sub-command, which will be described
below.  In some use cases, `fetch` sub-command may not frequently used.

Listing Mails
=============

Users can list mails of specific mailing list on the manifest file via `list`
sub-command.  By default, it lists the downloaded mails of the mailing list
that sent within last three days.  Users can let the command to do dowloading
of the mails together via `--fetch` option.  The sent time range of the mails
to list can be adjusted using `--since` and `--until` options.

In addition to the sent dates range, users can filter mails on the list by
author of the mail, keywords on subject or body, whether those are newly
started threads, via `--author`, `--subject_contains`, `--contains`, and
`--new` options, respectively.

The list shows all mails grouped by threads and sort the threads by sent date
of the latest mail of each thread.  Mails in each thread are sorted in the
reply order.  Users can show only first mail of each thread using `--collapse`
option.  It could be useful for mailing lists that people send huge amount of
mails every day.  Threads sorting key can also be customized using
`--sort_threads_by` option.  `--descend` option makes the sorting be done in
descendent order.  `--hot` option is a short cut for sorting threads by number
of comments in descendent way.

The sub-command support not only mailing lists on the manifest file, but more
sources.  All types of the supported sources of mails are as below.

- mailing lists.  Name of the mailing lists on the manifest can be passed.
- mbox files.  Paths to the mbox files of the mails can be passed.
- Special keyword, 'clipboard'.  If this keyword is passed as source of mails,
  the command assumes users have copied mbox-format string of the mails to list
  on the clipboard, read the clipboard, and show the mails.
- `hkml tag`-added tags.  Users can add arbitrary tags to specific mails using
  `hkml tag` command, which explained below.  The tags can be used here.
- Nothing.  If no source of mails is given, `hkml list` shows the
  last-generated list output again.

Below example lists mails that sent to [DAMON](https://damonitor.github.io/)
mailing list from 2024-02-15 to 2024-02-17.

```
$ hkml list damon --fetch --since 2024-02-15 --until 2024-02-17 --min_nr_mails 0
# 9 mails, 2 threads, 2 new threads
# 9 patches, 2 series
# oldest: 2024-02-16 11:40:23-08:00
# newest: 2024-02-16 16:58:42-08:00
[0] [PATCH 0/5] Docs/mm/damon: misc readability improvements (SeongJae Park, 24/02/16 16:58)
[1]   [PATCH 1/5] Docs/mm/damon/maintainer-profile: fix reference links for mm-[un]stable tree
      (SeongJae Park, 24/02/16 16:58)
[2]   [PATCH 2/5] Docs/mm/damon: move the list of DAMOS actions to design doc (SeongJae Park,
      24/02/16 16:58)
[3]   [PATCH 3/5] Docs/mm/damon: move DAMON operation sets list from the usage to the design
      document (SeongJae Park, 24/02/16 16:58)
[4]   [PATCH 4/5] Docs/mm/damon: move monitoring target regions setup detail from the usage to
      the design document (SeongJae Park, 24/02/16 16:58)
[5]   [PATCH 5/5] Docs/admin-guide/mm/damon/usage: fix wrong quotas diabling condition
      (SeongJae Park, 24/02/16 16:58)
[6] [PATCH 0/2] mm/damon: fix quota status loss due to online tunings (SeongJae Park, 24/02/16
    11:40)
[7]   [PATCH 1/2] mm/damon/reclaim: fix quota stauts loss due to online tunings (SeongJae
      Park, 24/02/16 11:40)
[8]   [PATCH 2/2] mm/damon/lru_sort: fix quota status loss due to online tunings (SeongJae
      Park, 24/02/16 11:40)
```

The output maybe intuitive to understand.  The first column of the each mail is
called index or identifier of the mail, and be used by other sub-commands that
will be described below.

Listing Entire Thread of a Given Mail
=====================================

On huge mailing list, reading all `hkml list` output takes time.  Also, because
`hkml list` lists mails that sent in user-specified time range (last three days
by default), some old mails of some threads may not listed.  Users can list all
mails of a specific threads containing a specific mail using `thread`
sub-command.  The mail of the thread can be specified by passing the mail
identifier of the mail to the sub-command.  The mail identifier should be that
of previously generated list.

For example, below command shows the thread of the third mail on the above
`hkml list` output.

```
$ hkml thread 3
# 6 mails, 1 threads, 1 new threads
# 6 patches, 1 series
# oldest: 2024-02-16 16:58:37-08:00
# newest: 2024-02-16 16:58:42-08:00
[0] [PATCH 0/5] Docs/mm/damon: misc readability improvements (SeongJae Park, 24/02/16 16:58)
[1]   [PATCH 1/5] Docs/mm/damon/maintainer-profile: fix reference links for mm-[un]stable tree
      (SeongJae Park, 24/02/16 16:58)
[2]   [PATCH 2/5] Docs/mm/damon: move the list of DAMOS actions to design doc (SeongJae Park,
      24/02/16 16:58)
[3]   [PATCH 3/5] Docs/mm/damon: move DAMON operation sets list from the usage to the design
      document (SeongJae Park, 24/02/16 16:58)
[4]   [PATCH 4/5] Docs/mm/damon: move monitoring target regions setup detail from the usage to
      the design document (SeongJae Park, 24/02/16 16:58)
[5]   [PATCH 5/5] Docs/admin-guide/mm/damon/usage: fix wrong quotas diabling condition
      (SeongJae Park, 24/02/16 16:58)
```

If the system is having [b4](https://b4.docs.kernel.org/) installed, the
command downloads whole mails of the thread and shows the list.  If the system
is not having `b4`, only the mails of the thread in the previously generated
list is listed.  Note that the mail identifiers are newly generated when `b4`
is used.

Reading Mails
=============

Users can open the content of the mail using `open` subcommand.  It receives
the identifier of the mail to read.  The identifier should be that of the last
generated `list` or `thread` output.

For example, below command shows the 18-th mail of the above list.

```
$ hkml open 3
Local-Date: 2024-02-16 16:58:40-08:00
Date: Fri, 16 Feb 2024 16:58:40 -0800
Subject: [PATCH 3/5] Docs/mm/damon: move DAMON operation sets list from the usage to the design document
Message-Id: <20240217005842.87348-4-sj@kernel.org>
From: SeongJae Park <sj@kernel.org>
To: Andrew Morton <akpm@linux-foundation.org>
CC: SeongJae Park <sj@kernel.org>, Jonathan Corbet <corbet@lwn.net>, damon@lists.linux.dev, linux-mm@kvack.org, linux-doc@vger.kernel.org, linux-kernel@vger.kernel.org

The list of DAMON operation sets and their explanation, which may better
to be on design document, is written on the usage document.  Move the
detail to design document and make the usage document only reference the
design document.

Signed-off-by: SeongJae Park <sj@kernel.org>
[...]
```

Tagging
=======

Some classification of mails, e.g., important, unread, to-read-next, etc, can
be helpful for managing flooding mails.  Users can add, remove, or list tags
for mails using 'hkml tag'.  The command receives a sub-command for the three
different actions.

`hkml list` supports tags as source of the mails to list up.  Users can
therefore use `hkml list` to list mails of a specific tag.  Below example lists
mails of a tag `tag_damon`.

```
$ hkml list tag_damon
[...]
[0] Re: [PATCH 1/2] mm/damon/sysfs: Implement recording feature (cuiyangpei, 24/02/05 19:26)
[1] [PATCH] mm/damon/sysfs: handle 'state' file inputs for every sampling interval if possible
    (SeongJae Park, 24/02/05 18:51)
```

`hkml tag add`
--------------

Add tags to a specific mail.  The mail could be specified with the index of the
mail from the last-generated list or thread output.  Tags can be any arbitrary
string.  Below example adds three tags namely `tag_example`, `damon_patch`, and
`not_yet_merged` to the fifth mail of the last-generated list output.

```
$ hkml tag add 5 tag_example damon_patch not_yet_merged
```

`hkml tag list`
---------------

Users can show generated tags using `hkml tag list` command like below:

```
$ hkml tag list
tag_damon: 2 mails
tag_example: 1 mails
damon_patch: 1 mails
not_yet_merged: 1 mails
```

`hkml tag remove`
-----------------

Users can remove tags from a specific mail using `hkml tag remove` command.
The mail to remove the tags from can be specified by the index of the mail from
the last-generated list or thread output.  Below example removes tag
`tag_damon` from the 0-th mail on the list and confirm it has removed using
`hkml tag list`.

```
$ hkml tag remove 0 tag_damon
$ hkml tag list
tag_damon: 1 mails
tag_example: 1 mails
damon_patch: 1 mails
not_yet_merged: 1 mails
```

Replying
========

Users can reply to specific mail on the last generated list, using `reply`
sub-command.  Similar to `thread` and `open`, it receives the identifier of the
mail to reply for, on the last generated `list` or `thread` output.

The command formats reply mail for the given mail and open VIM for the user's
interactive writing of the content.  Once the user finishes writing it and
close the editor, the command will show the content of the written reply mail
and ask it is ok to send the mail.  If the user answers the mail is correct and
ok to send, `reply` sub-command will send it.  If the user answers to not send
the mail, `reply` sub-command will further ask if the user want to delete the
draft or save it for further edit.

For example,

```
$ hkml reply 3
[...] # hkml reply open VIM.  Below is an example output after closing VIM.

Will send above mail.  Okay? [y/N] n
Leave the draft message? [Y/n] y
The draft message is at /tmp/hkml_reply_py9o_yec
```

Note that `hkml` send mail using `git send-email`.  Hence `git send-email`
should be configured correctly on the user's system.

Forwarding
==========

Users can forward a specific mail on the last generated list, using 'forward'
sub-command.  Similar to `thread` and `open`, it receives the identifier of the
mail to forward, on the last generated `list` or `thread` output.  Users can
specify subject, recipients, Cc list, etc via command line.  Then `forward`
sub-command formats the basic mail, and let the user additionally make more
edits interactively and finally send it, in a way pretty similar to that of
`reply`.  Again, `git send-email` setup is required.

Writing New Mails
=================

Users can write new mail in a way similar to `reply` sub-command, using `write`
sub-command.  Users can specify subject, recipients, Cc list, etc via command
line.  Then `write` sub-command formats the basic mail, and let the user
additionally make more edits interactively and finally send it, in a way pretty
similar to that of `reply`.  Again, `git send-email` setup is required.

Exporting Mails
===============

Users can export specific mails on the last `hkml list`-generated list to a
`mbox` file, using `export` sub-command.  It receives the path to the file that
will save the exported mail.  The file name should have `.mbox` suffix.  Users
can specify which mails from the list need to be exported via `--range` option
of the sub-command.

For example, below exports the first to fourth mails from above example mails
list to `foo.mbox` file, and then lists the exported mails in it again.

```
$ hkml export --range 0 4 foo.mbox
$ hkml list foo.mbox --since 2024-02-15 --until 2024-02-17
[...]
[0] [PATCH 0/5] Docs/mm/damon: misc readability improvements (SeongJae Park, 24/02/16 16:58)
[1]   [PATCH 1/5] Docs/mm/damon/maintainer-profile: fix reference links for mm-[un]stable tree
      (SeongJae Park, 24/02/16 16:58)
[2]   [PATCH 2/5] Docs/mm/damon: move the list of DAMOS actions to design doc (SeongJae Park,
      24/02/16 16:58)
[3]   [PATCH 3/5] Docs/mm/damon: move DAMON operation sets list from the usage to the design
      document (SeongJae Park, 24/02/16 16:58)
```

Users could also import the mbox file on their other mbox-supporting mail
client.

Monitoring Mails
================

Users can monitor new mails to specific mailing lists using `hkml monitor`
command.  Using this, users can get periodic notification of summary or updates
on specific mail threads that the user is not already in the loop, without
subscribing to the mailing list.  It works with sub-sub commands, `add`,
`status`, `remove`, and `start`.

`hkml monitor add`
------------------

`add` command adds monitoring request.  Users can specify
- the mailing lists to monitor,
- How often the monitoring should be done,
- what mails should be filtered in/out from the new mails,
- how the monitored mails should be displayed, and
- how the monitoring result should be delivered to users via command line
  options.

The command line options for specifying what mails to filtered and how those
should be displayed are very similar to that of `list` command.

It provides the monitoring results via the termina with some execution logs by
default, but users can asks it to send the new findings via sending emails to
specific addresses, or writing to specific files.

For example, users ask `hkml` to monitor updates to the `DAMON Beer/Coffee/Tea
chat series`
[thread](https://lore.kernel.org/r/20220810225102.124459-1-sj@kernel.org) for
every hour, format notification text with lore links for found new mails, and
send the notification text to their personal email address, like below:

```
$ hkml monitor add damon \
    --subject_keywords "DAMON Beer/Coffee/Tea chat series" \
    --monitor_interval 3600 --lore --noti_mails $YOUR_EMAIL_ADDRESS \
    --name "DAMON chat series monitoring"
```

`hkml monitor remove`
---------------------

Remove added monitoring requests.  User can specify the request to remove using
the index of the request on the requests list that can be shown via `hkml
monitor status`, or the name of the request which the user can set with `hkml
monitor add` command.

`hkml monitor status`
---------------------

Show status of the monitoring, including list of currently added monitoring
requests.

`hkml monitor start`
--------------------

Start the requested monitoring.  Monitoring requests that added after
monitoring is started is not automatically added to the running instance.  You
should start a new instance for new requests.  To stop running instance, you
can simply Ctrl-C.
