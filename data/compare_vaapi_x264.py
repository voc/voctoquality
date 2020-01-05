#!/usr/bin/env python3
import util

# Reference video
ref = "reference.mkv"

# Should return a dict of formats
# Each format should be a dict containing ffmpeg options like:
# {"opts": "-i ..."}
#
# Additional custom keys can be added for easier plotting
def formats():
    ret = {}

    # Use a 1:1 copy to check whether the input itself reaches a score of 100
    # otherwise there's some problems with your reference content
    #ret["ref"] = {"opts": f"-i {ref} -c:v copy"}

    # generate formats for different bitrates
    for rate in [3000, 9000, 15000]:
        ret[f"vaapi_{rate}"] = {
            "encoder": "vaapi",
            "rate": rate,
            "opts": f"""
    -vaapi_device /dev/dri/renderD128
    -hwaccel vaapi -hwaccel_output_format vaapi
    -i {ref}
    -vf 'format=nv12|vaapi,hwupload'
    -c:v h264_vaapi -compression_level 1
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate*2}k
"""}

        ret[f"x264_{rate}"] = {
            "encoder": "x264",
            "rate": rate,
            "opts": f"""
    -i {ref}
    -c:v libx264 -preset:v veryslow -crf:v 18
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate*2}k
"""}
    return ret

# custom plotting
def plot(formats, scores):
    import matplotlib.pyplot as plt

    encoders = set(fmt["encoder"] for fmt in formats.values())
    rates = set(fmt["rate"] for fmt in formats.values())
    plots = []
    for encoder in encoders:
        x = []
        y = []
        for rate in sorted(rates):
            fmt = f"{encoder}_{rate}"
            x.append(scores[fmt]["rate"] / 1e3)
            y.append(scores[fmt]["score"])
        print(encoder, x, y)
        plots.append(plt.plot(x, y, "+-")[0])

    plt.axis([0, 20, 0, 100])
    plt.title("Bitrate vs VMAF score for x264/vaapi")
    plt.xlabel("Avg. Bitrate in Mbit/s")
    plt.ylabel("Avg. VMAF score")
    plt.legend(plots, encoders)
    plt.savefig("bitrates.pdf")
    plt.show()

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", choices=["transcode", "plot"],
        help="do only some of the tasks", default="all")

    args = parser.parse_args()
    fmts = formats()

    # transcode creates subformats and calculates scores, speed and actual rate
    if args.task == "all" or args.task == "transcode":
        scores = util.transcode(ref, fmts, scale=None)
        with open("tmp/scores.json", "w") as f:
            json.dump(scores, f)

    # do plots
    scores = None
    if args.task == "all" or args.task == "plot":
        with open("tmp/scores.json", "r") as f:
            scores = json.load(f)
        plot(fmts, scores)

if __name__ == "__main__":
    main()
