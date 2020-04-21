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

def calc_score(reference, coded, scale=None):
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

def transcode(ref, formats, scale=None, tmpdir="tmp"):
    os.makedirs("tmp", exist_ok=True)
    results = {}

    # prepare reference (if this is not yuv the scores are strange...)
    refpath = os.path.join(tmpdir, "ref.nut")
    cmd = f"""
ffmpeg -y -hide_banner -v warning
-i {ref}
-c:v rawvideo -an
{refpath}
"""
    try:
        subprocess.check_call(shlex.split(cmd))
    except subprocess.CalledProcessError:
        print(f"Failed to decode ref '{ref}'")
        return results

    progresspath = os.path.join(tmpdir, "progress")
    for fmt in formats:
        results[fmt] = {}

        # encode input
        codedpath = os.path.join(tmpdir, f"{fmt}.nut")
        cmd = f"""
ffmpeg -y -hide_banner -v warning -stats -progress {progresspath}
{formats[fmt]["opts"].replace("$ref", refpath)}
    -an
    {codedpath}
"""
        try:
            subprocess.check_call(shlex.split(cmd))
        except subprocess.CalledProcessError:
            print(f"Failed to encode {fmt}")
            continue

        # read final speed from progress
        speed = 0
        with open(progresspath, "r") as f:
            progress = f.read().split("progress=continue")[-1]
            for line in progress.split("\n"):
                match = re.match("^speed=([\d.]+)x$", line)
                if match is not None:
                    results[fmt]["speed"] = float(match[1])

        # probe real coded bitrate
        results[fmt]["rate"] = probe_rate(codedpath)

        # calculate vmaf score
        scores = calc_score(ref, codedpath, scale)
        if scores is None:
            print(f"Failed to score {fmt}")
            continue

        # Calculate different aggregates
        score_mean = sum(scores) / len(scores)
        print("Mean:", score_mean)
        results[fmt]["score_mean"] = score_mean

        score_harm_mean = len(scores) / sum(1 / (score + 1) for score in scores) - 1
        print("Harmonic mean:", score_harm_mean)
        results[fmt]["score_harm_mean"] = score_harm_mean

        score_10th_pct = sorted(scores)[math.ceil(0.1*len(scores))]
        print("10th pctile:", score_10th_pct)
        results[fmt]["score_10th_pct"] = score_10th_pct

        print("Min:", min(scores))
        results[fmt]["score_min"] = min(scores)

    return results

def init(formats, plot):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", choices=["transcode", "plot"],
        help="do only some of the tasks", default="all")
    parser.add_argument("ref", help="reference video")

    args = parser.parse_args()

    # transcode creates subformats and calculates scores, speed and actual rate
    if args.task == "all" or args.task == "transcode":
        scores = transcode(args.ref, formats, scale=None)
        with open("tmp/scores.json", "w") as f:
            json.dump(scores, f)

    # do plots
    scores = None
    if args.task == "all" or args.task == "plot":
        with open("tmp/scores.json", "r") as f:
            scores = json.load(f)
        plot(formats, scores)


