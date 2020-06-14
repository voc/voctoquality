import subprocess
import shlex
import re
import json
import math
from os import path


def ffprobe(path):
    cmd = f"""
ffprobe -hide_banner -show_format -show_streams
    -loglevel quiet -print_format json
    {path}
"""
    try:
        output = subprocess.check_output(shlex.split(cmd))
        result = json.loads(output.decode("utf-8"))
    except (subprocess.CalledProcessError,):
        return None

    return result


def probe_rate(path):
    result = ffprobe(path)
    if result is None:
        return None

    bitrate = int(result["format"]["bit_rate"]) / 1000
    return bitrate


class EncodeFailed(Exception):
    pass


class DecodeFailed(Exception):
    pass


class ScoreFailed(Exception):
    pass


def decode(src, dst):
    """Decodes media file at src and stores it at dst"""
    cmd = f"""
ffmpeg -y -hide_banner -nostats -v warning
    -i {src}
    -c:v rawvideo -an
    {dst}
"""
    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        raise DecodeFailed(f"Failed to decode '{src}' - {err}")


def calc_score(reference, coded, scale=None):
    """Computes vmaf scores for encoded video content"""
    scorepath = f"{coded}.json"

    # scale_filter = "scale=w=0:h=0"
    # if scale is not None:
    #     scale_filter = f"scale={scale}:flags=bicubic"

    rate = f"""
ffmpeg -y -hide_banner -v warning
    -i {coded} -i {reference}
    -filter_complex "[0:v][1:v]libvmaf=log_fmt=json:log_path={scorepath}:n_subsample=3"
    -f null -
"""
    try:
        subprocess.check_call(shlex.split(rate))
    except subprocess.CalledProcessError:
        return None

    with open(scorepath, "r") as f:
        data = json.load(f)

        return [frame["metrics"]["vmaf"] + 1 for frame in data["frames"]]


def transcode(ref, desc, opts, scale, tmpdir):
    """
    Transcodes reference to a specific format and computes the vmaf score
    of the resulting file.

    | Arguments:
    | ref: Path to raw YUV reference-file
    | desc: format descriptor
    | opts: ffmpeg option string, must contain '-i $ref' as reference input
    |   placeholder
    | tmpdir: directory to store temporary files in

    """
    result = {}

    # encode input
    print(f"Transcoding descriptor: {desc}")
    codedpath = path.join(tmpdir, f"{desc}.nut")
    progresspath = path.join(tmpdir, "progress")
    cmd = f"""
ffmpeg -y -hide_banner -v warning -stats -progress {progresspath}
{opts.replace("$ref", ref)}
-an
{codedpath}
"""
    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        raise EncodeFailed(f"Failed at format {desc} - {err}")

    # read final speed from progress
    with open(progresspath, "r") as f:
        progress = f.read().split("progress=continue")[-1]
        for line in progress.split("\n"):
            match = re.match("^speed=([\d.]+)x$", line)
            if match is not None:
                result["speed"] = float(match[1])

    # probe real coded bitrate
    result["rate"] = probe_rate(codedpath)

    # calculate vmaf score
    scores = calc_score(ref, codedpath, scale)
    if scores is None:
        raise ScoreFailed(f"Failed to compute score for {desc}")

    # Calculate different aggregates
    score_mean = sum(scores) / len(scores)
    print("Mean:", score_mean)
    result["score_mean"] = score_mean

    score_harm_mean = len(scores) / sum(1 / (score + 1) for score in scores) - 1
    print("Harmonic mean:", score_harm_mean)
    result["score_harm_mean"] = score_harm_mean

    score_10th_pct = sorted(scores)[math.ceil(0.1*len(scores))]
    print("10th pctile:", score_10th_pct)
    result["score_10th_pct"] = score_10th_pct

    print("Min:", min(scores))
    result["score_min"] = min(scores)

    return result


def valid_reference(ref, tmpdir):
    """
    Tests the scoring of a reference file. A copy encode should yield a score
    of close to 100. Otherwise there are problems with the reference
    such as muxing errors.

    Returns: True if reference is ok
    """
    rawref = path.join(tmpdir, "ref.nut")
    try:
        decode(ref, rawref)
    except DecodeFailed as err:
        print(f"Reference decode failed: {err}")
        return False

    try:
        sanity_result = transcode(rawref, "sanity", "-i $ref -c:v copy", None, tmpdir)

    except (EncodeFailed, ScoreFailed) as err:
        print(f"Sanity encode failed: {err}")
        return False

    if (sanity_result["score_min"] < 95 or sanity_result["score_harm_mean"] < 98):

        print(f"Sanity score for reference file '{ref}' not close to 100. \
            Please fix your reference!")

        return False

    return True
