import argparse
import os
import math
import json
import shlex, subprocess
import re

def ffprobe(path):
    try:
        output = subprocess.check_output(["ffprobe", "-hide_banner", "-show_format", "-show_streams", "-loglevel", "quiet", "-print_format", "json", path])
        result = json.loads(output.decode("utf-8"))
    except (subprocess.CalledProcessError,):
        print("Error: failed to probe %s" % path)
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
ffmpeg -y -hide_banner -v warning
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
    scale_filter = "scale=w=0:h=0"
    if scale is not None:
        scale_filter = f"scale={scale}:flags=bicubic"

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

def transcode_format(ref, name, fmt, scale, tmpdir):
    """
    Transcodes reference to a specific format and computes the vmaf score
    of the resulting file.

    | Arguments:
    | ref: Path to raw YUV reference-file
    | name: format name
    | fmt: dict with format description
    | tmpdir: directory to store temporary files in

    """
    result = {}

    # encode input
    print(f"Transcoding format: {name}")
    codedpath = os.path.join(tmpdir, f"{name}.nut")
    progresspath = os.path.join(tmpdir, "progress")
    cmd = f"""
ffmpeg -y -hide_banner -v warning -stats -progress {progresspath}
{fmt["opts"].replace("$ref", ref)}
-an
{codedpath}
"""
    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        raise EncodeFailed(f"Failed at format {name} - {err}")

    # read final speed from progress
    speed = 0
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
        raise ScoreFailed(f"Failed to compute score for {name}")

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

def transcode(ref, formats, scale=None, tmpdir="tmp"):
    """
    Transcodes a reference file to a list of formats and
    computes the vmaf score for each one.

    | Arguments:
    | ref: reference file
    | formats: dict of format name -> format description
    | scale: scale content before determining score (Scale of transcoded content and reference must match or the score will be wrong)
    | tmpdir: directory to store transcoded files in
    """
    os.makedirs("tmp", exist_ok=True)
    results = {}

   # Decode reference (Must be YUV or the VMAF scores will be wrong...)
    rawref = os.path.join(tmpdir, "ref.nut")
    try:
        decode(ref, rawref)
    except DecodeFailed as err:
        print("Failed to decode reference file: {err}")
        return results

    # Test reference file, a copy transcode should yield a score of ~= 100
    fmt = {"opts": "-i $ref -c:v copy"}
    try:
        sanity_result = transcode_format(rawref, "sanity", fmt, scale, tmpdir)
    except (EncodeFailed, ScoreFailed) as err:
        print("Sanity encode failed: {err}")
        return results

    if sanity_result["score_min"] < 95 or sanity_result["score_harm_mean"] < 98:
        print(f"Sanity score for reference file '{ref}' not close to 100. Please fix your reference!")
        return results

    # Transcoding to user formats
    for name in formats:
        try:
            fmt = formats[name]
            results[name] = transcode_format(rawref, name, fmt, scale, tmpdir)
        except (EncodeFailed, ScoreFailed) as err:
            print(err)

    return results

def init(formats, plot):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", choices=["all", "transcode", "plot"],
        help="do only some of the tasks", default="all")
    parser.add_argument("references", nargs="+", help="reference videos")

    args = parser.parse_args()
    print("Reference videos:", args.references)

    # transcode creates subformats and calculates scores, speed and actual rate
    if args.task == "all" or args.task == "transcode":
        scores = {}
        for reference in args.references:
            name = os.path.basename(reference)
            print(f"Processing reference: {reference}")
            scores[name] = transcode(reference, formats, scale=None)
        with open("tmp/scores.json", "w") as f:
            json.dump(scores, f)

    # do plots
    scores = None
    if args.task == "all" or args.task == "plot":
        with open("tmp/scores.json", "r") as f:
            scores = json.load(f)

        for reference in args.references:
            name = os.path.basename(reference)
            if name not in scores:
                print(f"Score for reference '{reference}' not found")
                continue
            score = scores[name]
            plot(name, formats, score)

aggregations = ["harm_mean", "10th_pct", "min"]
aggregationLabels = ["Harmonic Mean", "10th Percentile", "Minimum"]
