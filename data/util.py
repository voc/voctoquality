import os
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
        return data["VMAF score"]

def transcode(ref, formats, scale=None):
    os.makedirs("tmp", exist_ok=True)
    scores = {}
    for fmt in formats:
        scores[fmt] = {}

        # encode input
        codedpath = os.path.join("tmp", f"{fmt}.mkv")
        cmd = f"""
ffmpeg -y -hide_banner -v warning -stats -progress tmp/progress
{formats[fmt]["opts"]}
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
        with open("tmp/progress", "r") as f:
            progress = f.read().split("progress=continue")[-1]
            for line in progress.split("\n"):
                match = re.match("^speed=([\d.]+)x$", line)
                if match is not None:
                    scores[fmt]["speed"] = float(match[1])

        # probe real coded bitrate
        scores[fmt]["rate"] = probe_rate(codedpath)

        # calculate vmaf score
        score = calc_score(ref, codedpath, scale)
        if score is None:
            print(f"Failed to score {fmt}")
            continue

        scores[fmt]["score"] = score


    return scores
