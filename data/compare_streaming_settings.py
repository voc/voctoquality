#!/usr/bin/env python3
# Script to compare different VAAPI codecs to x264 and libvpx-vp9 software codecs
# The codec settings are taken from the C3VOC production streaming setup
import util

# Should return a dict of formats
# Each format should be a dict containing ffmpeg options like:
# {"opts": "-i ..."}
#
# Additional custom keys can be added for easier plotting
def formats():
    ret = {}

    # generate formats for different bitrates
    for rate in [1000, 1400, 2000, 2800, 4000, 5200]:
        for codec in ["vp9", "h264", "hevc"]:
            ret[f"vaapi_{codec}_{rate}"] = {
                "encoder": "vaapi",
                "codec": codec,
                "rate": rate,
                "opts": f"""
    -vaapi_device /dev/dri/renderD128
    -hwaccel vaapi -hwaccel_output_format vaapi
    -i $ref
    -vf 'format=nv12|vaapi,hwupload'
    -c:v {codec}_vaapi
    -keyint_min:v 75 -g:v 75
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate}k
"""}

        ret[f"x264_h264_{rate}"] = {
            "encoder": "x264",
            "codec": "h264",
            "rate": rate,
            "opts": f"""
    -i $ref
    -c:v libx264 -preset:v veryfast
    -profile:v main -flags +cgop
    -threads:v 0 -g:v 75
    -crf:v 21
    -maxrate:v {rate}k -bufsize {rate}k
"""}

        ret[f"libvpx_vp9_{rate}"] = {
            "encoder": "libvpx",
            "codec": "vp9",
            "rate": rate,
            "opts": f"""
    -i $ref
    -c:v libvpx-vp9
    -deadline:v realtime -cpu-used:v 8
    -threads:v 8
    -frame-parallel:v 1 -tile-columns:v 2
    -keyint_min:v 75 -g:v 75
    -crf:v 23
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate}k
"""}
    return ret

# custom plotting
def plot_rates(name, formats, scores):
    import matplotlib.pyplot as plt

    encoders = set(fmt["encoder"] for fmt in formats.values())
    codecs = set(fmt["codec"] for fmt in formats.values())
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
            for codec in sorted(codecs):
                x = []
                y = []
                for rate in sorted(rates):
                    fmt = f"{encoder}_{codec}_{rate}"
                    if not fmt in scores:
                        continue
                    x.append(scores[fmt]["rate"] / 1e3)
                    y.append(scores[fmt][f"score_{agg}"])

                if len(x) > 0:
                    print("  rates", agg, encoder, codec, x, y)
                    plots.append(ax.plot(x, y, "+-")[0])
                    legends.append(f"{encoder}-{codec}")

        ax.axis([0, 7, 0, 100])
        ax.set_xlabel("Avg. Bitrate in Mbit/s")
        ax.set_ylabel(f"{label} VMAF score")
        ax.legend(plots, legends)
        ax.grid(True)
    fig.tight_layout()
    plt.savefig(f"bitrates_{name}.pdf")
    plt.close()

def plot_speed(name, formats, scores):
    import matplotlib.pyplot as plt

    encoders = set(fmt["encoder"] for fmt in formats.values())
    codecs = set(fmt["codec"] for fmt in formats.values())
    rates = set(fmt["rate"] for fmt in formats.values())
    plots = []
    legends = []
    for encoder in sorted(encoders):
        for codec in sorted(codecs):
            x = []
            y = []
            for rate in sorted(rates):
                fmt = f"{encoder}_{codec}_{rate}"
                if not fmt in scores or not "speed" in scores[fmt]:
                    continue
                x.append(scores[fmt]["rate"] / 1e3)
                y.append(scores[fmt]["speed"])

            if len(x) > 0:
                print("  speeds", encoder, codec, x, y)
                plots.append(plt.plot(x, y, "+-")[0])
                legends.append(f"{encoder}-{codec}")

    plt.axis([0, 7, 0, 10])
    plt.title("Coding Speed for vaapi/libvpx")
    plt.xlabel("Avg. Bitrate in Mbit/s")
    plt.ylabel("Coding Speed")
    plt.legend(plots, legends)
    plt.grid(True)
    plt.savefig(f"speed_{name}.pdf")
    plt.close()

def plot(name, formats, scores):
    print("plot", name)
    plot_rates(name, formats, scores)
    plot_speed(name, formats, scores)
    print("")

if __name__ == "__main__":
    util.init(formats(), plot)
