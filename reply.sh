#!/bin/bash

bindir=$(dirname "$0")

reply_file=$(mktemp hkml-reply-XXXX)

xclip -o | "$bindir/hkml" format_reply > "$reply_file"
vi "$reply_file"

cat "$reply_file"
echo
read -rp "Will send above mail.  Okay? [y/N] " answer
if [ ! "$answer" = "y" ]
then
	read -rp "Leave the reply message? [Y/n] " answer
	if [ "$answer" = "n" ]
	then
		rm "$reply_file"
	else
		echo "your reply message is at $reply_file"
	fi
	exit
fi

"$bindir/hkml" send "$reply_file"
rm "$reply_file"
