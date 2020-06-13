import json
import subprocess
import shlex
from os import path, rename, makedirs, stat

class ReferencePrepareFailed(Exception):
    pass

class InvalidSourceHash(Exception):
    pass

def hash_file(path):
    import hashlib
    BLOCKSIZE = 1024 * 16
    hasher = hashlib.md5()
    with open(path, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def check_reference(source, ref):
    digest = hash_file(ref)
    if "hash" in source:
        if digest != source["hash"]:
            raise InvalidSourceHash(f"Hash for reference {source['name']} is {digest}, expected {source['hash']}")
    else:
        print(f"Reference {source['name']} md5 is {digest} ")

def prepare_reference(src, dst, skip="", duration=""):
    if skip:
        skip = "-ss " + skip
    if duration:
        duration = "-to " + duration

    cmd = f"""
ffmpeg -y -hide_banner -v error {skip}
    -i {src}
    -c:v ffvhuff -an {duration}
    -r 25 -s 1920x1080 -sws_flags bicubic -pix_fmt yuv420p
    {dst}
"""
    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        raise ReferencePrepareFailed(f"Failed to prepare '{src}' - {err}")

def ensure_references(sourcefile, env):
    """
    Make sure all sources and derived references are present

    Returns: list of reference files
    """
    with open(sourcefile, "r") as f:
        sources = json.load(f)

    makedirs(env["refdir"], exist_ok=True)

    references = []
    for source in sources:
        ref = path.join(env["refdir"], f"{source['name']}.nut")
        tmpref = path.join(env["refdir"], f"{source['name']}.tmp.nut")

        duration = ""
        skip = ""
        if "duration" in source:
            duration = source["duration"]
        if "from" in source:
            skip = source["from"]

        redownload = False
        try:
            stat(ref)
            check_reference(source, ref)

        except FileNotFoundError:
            redownload = True

        if redownload:
            print(f"Downloading reference: {source['name']}")
            prepare_reference(source["url"], tmpref, skip, duration)
            check_reference(source, tmpref)
            rename(tmpref, ref)

        references.append(ref)

    return references




