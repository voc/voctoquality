#!/usr/bin/env python3
import util

# Should return a dict of formats
# Each format should be a dict containing ffmpeg options like:
# {"opts": "-i ..."}
#
# Additional custom keys can be added for easier plotting
def formats():
    ret = {}

    # generate formats for different bitrates
    for rate in [3000, 9000, 15000]:
        ret[f"vaapi_{rate}"] = {
            "encoder": "vaapi",
            "rate": rate,
            "opts": f"""
    -vaapi_device /dev/dri/renderD128
    -hwaccel vaapi -hwaccel_output_format vaapi
    -i $ref
    -vf 'format=nv12|vaapi,hwupload'
    -c:v h264_vaapi
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate*2}k
"""}

        ret[f"x264_{rate}"] = {
            "encoder": "x264",
            "rate": rate,
            "opts": f"""
    -i $ref
    -c:v libx264 -preset:v medium -crf:v 18
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate*2}k
"""}
    return ret

# custom plotting
def plot(name, formats, scores):
    import matplotlib.pyplot as plt

    encoders = set(fmt["encoder"] for fmt in formats.values())
    rates = set(fmt["rate"] for fmt in formats.values())
    count = len(util.aggregations)

    plt.title(f"VMAF score vs Bitrate for VA-API/x264/libvpx")
    fig, axs = plt.subplots(count, 1, figsize=(8,count*5))
    for i in range(count):
        agg = util.aggregations[i]
        label = util.aggregationLabels[i]
        ax = axs[i]
        plots = []
        legends = []
        for encoder in sorted(encoders):
            x = []
            y = []
            for rate in sorted(rates):
                fmt = f"{encoder}_{rate}"
                if not fmt in scores:
                    continue
                x.append(scores[fmt]["rate"] / 1e3)
                y.append(scores[fmt][f"score_{agg}"])

            if len(x) > 0:
                print(encoder, x, y)
                plots.append(ax.plot(x, y, "+-")[0])
                legends.append(f"{encoder}")

        ax.axis([0, 20, 0, 100])
        ax.set_xlabel("Avg. Bitrate in Mbit/s")
        ax.set_ylabel(f"{label} VMAF score")
        ax.legend(plots, legends)
        ax.grid(True)
    fig.tight_layout()
    plt.savefig(f"bitrates_{name}.pdf")

if __name__ == "__main__":
    util.init(formats(), plot)
