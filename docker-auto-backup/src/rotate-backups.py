#!/usr/bin/env python3

#
# Python script for rotating old backups.
#
# This part is written in Python to improve compatibility between
# systems because remote backups are rotated by rsync'ing this
# script onto the remote system first. Using shell scripts across
# different machines is hard because different shells have some
# small differences.
#

import os
from os import DirEntry
from datetime import datetime
from typing import Dict
from argparse import ArgumentParser

BACKUP_EXT = "tar.gz.gpg"
DATETIME_FORMAT = "%Y-%m-%dT%H-%M-%S"

def find_backups(archive_dir: str) -> Dict[int, DirEntry]:
    """
    Find all backups from a directory.

    :param archive_dir: The directory path to search in.

    :return: A dictionary that contains DirEntry instances. The dictionary
             keys are generated based on the timestamps of the backups.

    :raises Exception: If the archive_dir path is not a directory.
    """

    global BACKUP_EXT
    global DATETIME_FORMAT

    backups = {}

    if not os.path.isdir(archive_dir):
        raise Exception("Archive path is not a directory.")

    for entry in os.scandir(archive_dir):
        # Skip directories.
        if not entry.is_file():
            print("Skipping file: {} (not a file)".format(entry.path))
            continue

        # Skip files with an incorrect extension.
        if not ".".join(entry.name.split(".")[-3:]) == BACKUP_EXT:
            print(
                "Skipping file: {} (wrong extension, expected: *.{})"
                .format(entry.path, BACKUP_EXT)
            )
            continue

        # Parse datetime from filename & skip files with invalid names.
        try:
            isostr = (entry.name.split("."))[0]
            dt = datetime.strptime(isostr, DATETIME_FORMAT)
        except ValueError:
            print(
                "Skipping file: {} (invalid name format, expected: {}.*)"
                .format(entry.path, DATETIME_FORMAT)
            )
            continue

        backups[int(dt.timestamp())] = entry

    return backups

def rotate_backups(archive_dir: str, keep: int) -> None:
    """
    Rotate backups in a directory.

    :param archive_dir: The directory path to work in.
    :param keep: The number of backups to keep.
    """

    b = find_backups(archive_dir)
    b_keys = sorted(b)
    b_rm = b_keys[:len(b_keys) - keep]

    print("Found {} backups in total.".format(len(b)))
    print("Remove: {}, Keep: {}.".format(len(b_rm), len(b) - len(b_rm)))

    for key in b_rm:
        print("unlink: " + b[key].path)
        os.unlink(b[key].path)

if __name__ == "__main__":
    ap = ArgumentParser(description="Rotate Docker volume backups")
    ap.add_argument(
        "--dir",
        "-d",
        metavar="PATH",
        type=str,
        required=True,
        help="Specify an archive directory path."
    )
    ap.add_argument(
        "--keep",
        "-k",
        metavar="N",
        type=int,
        required=True,
        help="Specify the number of backups to keep."
    )
    args = ap.parse_args()

    rotate_backups(args.dir, args.keep)
