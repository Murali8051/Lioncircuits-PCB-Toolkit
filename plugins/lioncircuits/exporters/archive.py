"""Zip helper for bundling Gerbers + drill files into one fab-ready archive."""

import os
import zipfile


def zip_directory(src_dir, zip_path, extensions=None):
    """Zip every file directly inside src_dir (non-recursive) into zip_path.

    If `extensions` is given (e.g. {'.gbr', '.drl', '.gbrjob'}), only files
    matching those extensions are included.
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(src_dir)):
            fpath = os.path.join(src_dir, fname)
            if not os.path.isfile(fpath):
                continue
            if extensions and os.path.splitext(fname)[1].lower() not in extensions:
                continue
            zf.write(fpath, arcname=fname)
    return zip_path
