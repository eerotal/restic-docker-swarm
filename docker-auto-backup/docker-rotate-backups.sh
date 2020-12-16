#!/bin/sh

set -e

get_file_index_by_timestamp() {
    dt="$(echo "$1" | cut -d'_' -f2 | cut -d'.' -f1)"
    date="$(echo "$dt" | cut -d'T' -f1)"
    time="$(echo "$dt" | cut -d'T' -f2 | sed s/-/:/g)"
    echo "$(date -d "${date}T${time}+00:00" +'%s')"
}

if [ $# -lt 2 ]; then
    echo "[ERROR] Missing arguments."
    echo "Usage: docker-rotate-backups.sh [ARCHIVE_DIR] [ROTATE_AFTER]"
    exit 1
fi
ARCHIVE_DIR="$1"
ROTATE_AFTER="$2"

# Find all backup files and prefix their names with indices
# derived from the timestamps of the files.
files_original=""
files_indexed=""
for f in $(ls -1A "$ARCHIVE_DIR"); do
    if [ -z "$(echo "$f" | grep .tar.gz.gpg)" ]; then continue; fi
    if [ ! -f "${ARCHIVE_DIR}/$f" ]; then continue; fi

    files_original="$files_original $f"

    index="$(get_file_index_by_timestamp "$f")"
    files_indexed="$files_indexed\n${index}_$f"
done
echo "[INFO] Found $(echo "$files_indexed" | wc -w) backups."

# Remove all but the last $ROTATE_AFTER files.
tmp="$(echo "$files_indexed" | sort | tail -n "$ROTATE_AFTER")"

# Remove the indices from the file names.
files_keep=""
for f in "$tmp"; do
    files_keep="$files_keep\n$(echo "$f" | cut -d'_' -f2-)"
done

echo "[INFO] Keeping newest $ROTATE_AFTER backups:"
echo "$files_keep" | sed '/^$/d' | sed "s:^:${ARCHIVE_DIR}:g"

# Remove all backups that are not included in the $files_keep list.
echo "[INFO] Removing older backups."
for f in $files_original; do
    if [ -z "$(echo "$files_keep" | grep "$f")" ]; then
        rm -fv "$ARCHIVE_DIR/$f"
    fi
done
