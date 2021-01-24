from libquality.profile import Profile as Base
from os import path


class Profile(Base):
    name = "voc-streaming"
    dimensions = ["encoder", "codec", "target_rate"]

    def formats(self):
        # generate formats for different bitrates
        for rate in [1000, 1400, 2000, 2800, 4000, 5200]:
            for codec in ["vp9", "h264", "hevc"]:
                yield {
                    "encoder": "vaapi",
                    "codec": codec,
                    "target_rate": rate,
                    "opts": f"""
    -vaapi_device /dev/dri/renderD128
    -hwaccel vaapi -hwaccel_output_format vaapi
    -i $ref
    -vf 'format=nv12|vaapi,hwupload'
    -c:v {codec}_vaapi
    -keyint_min:v 75 -g:v 75
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate}k
"""}

            for codec in ["h264", "hevc"]:
                yield {
                    "encoder": "nvenc",
                    "codec": codec,
                    "target_rate": rate,
                    "opts": f"""
    -i $ref
    -c:v {codec}_nvenc
    -keyint_min:v 75 -g:v 75
    -no-scenecut:v 1
    -pixel_format yuv420p
    -b:v {rate}k -maxrate:v {rate}k -bufsize {rate}k
"""}

            yield {
                "encoder": "x264",
                "codec": "h264",
                "target_rate": rate,
                "opts": f"""
    -i $ref
    -c:v libx264 -preset:v veryfast
    -profile:v main -flags +cgop
    -threads:v 0 -g:v 75
    -crf:v 21
    -maxrate:v {rate}k -bufsize {rate}k
"""}

            yield {
                "encoder": "libvpx",
                "codec": "vp9",
                "target_rate": rate,
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

    def plot(self, df, plotdir):
        self.plot_score_per_rate(df.copy(), plotdir)
        self.plot_score_per_ref(df.copy(), plotdir)
        self.plot_speeds(df.copy(), plotdir)

    def plot_score_per_rate(self, df, plotdir):
        import pandas as pd
        import matplotlib.pyplot as plt

        # label codecs
        df.loc[:, "oldenc"] = df["encoder"]
        df.loc[:, "encoder"] = df["oldenc"] + "-" + df["codec"]
        df.loc[lambda df: df['oldenc'] == "vaapi", "encoder"] = df["tag"] + "-" + df["codec"]

        # Group scores by target rate
        group = df.groupby(["target_rate", "encoder"])

        scores = group[["score_mean"]].mean().unstack().droplevel(0, axis=1)
        rates = group[["rate"]].mean().unstack().droplevel(0, axis=1)

        # But plot with real rate
        legend = []
        plt.rcParams["figure.figsize"] = (8, 6)
        for encoder in scores:
            data = pd.DataFrame({encoder: scores[encoder], "rate": rates[encoder]})
            plt.plot(data["rate"]/1000, data[encoder], "-+")
            legend.append(encoder)

        plt.legend(legend)

        plt.axis([0, 6, 0, 100])
        plt.title("Score")
        plt.xlabel("Avg. Bitrate in Mbit/s")
        plt.ylabel("Mean VMAF score over all references")
        plt.title("Score over Bitrate for VAAPI vs. Software codecs")
        plt.grid(True)
        plt.savefig(path.join(plotdir, "streaming_rates.pdf"))
        plt.close()

    def plot_score_per_ref(self, df, plotdir):
        import matplotlib.pyplot as plt

        # label codecs
        df.loc[:, "oldenc"] = df["encoder"]
        df.loc[:, "encoder"] = df["oldenc"] + "-" + df["codec"]
        df.loc[lambda df: df['oldenc'] == "vaapi", "encoder"] = df["tag"] + "-" + df["codec"]

        group = df.groupby(["encoder", "reference"])
        scores = group[["score_mean"]].mean().unstack("encoder").droplevel(0, axis=1)
        errors = group[["score_mean"]].mad().unstack("encoder").droplevel(0, axis=1)

        plt.rcParams["figure.figsize"] = (8, 6)
        scores.plot.bar(ylim=(0, 100), yerr=errors, capsize=2)
        plt.title("Codec comparison per reference file")
        plt.ylabel("Mean VMAF score + MAD")
        plt.subplots_adjust(bottom=0.2)
        plt.grid(True)
        plt.savefig(path.join(plotdir, "streaming_refs.pdf"))
        plt.close()

    def plot_speeds(self, df, plotdir):
        import pandas as pd
        import matplotlib.pyplot as plt

        df.loc[:, "encoder"] = df["tag"] + "-" + df["encoder"] + "-" + df["codec"]

        # Group scores by target rate
        group = df.groupby(["target_rate", "encoder"])
        speeds = group[["speed"]].mean().unstack().droplevel(0, axis=1)
        rates = group[["rate"]].mean().unstack().droplevel(0, axis=1)
        errors = group[["speed"]].mad().unstack().droplevel(0, axis=1)

        # But plot with real rate
        legend = []
        plt.rcParams["figure.figsize"] = (8, 6)
        for encoder in speeds:
            data = pd.DataFrame({encoder: speeds[encoder], "rate": rates[encoder]})
            plt.errorbar(data["rate"]/1000, data[encoder], yerr=errors[encoder], capsize=2)
            legend.append(encoder)

        plt.legend(legend)

        plt.axis([0, 6, 0, 10])
        plt.title("Coding Speed for vaapi/libvpx")
        plt.xlabel("Avg. Bitrate in Mbit/s")
        plt.ylabel("Encoding Speed in multiples of realtime")
        plt.title("Speed over Bitrate for VAAPI vs. Software codecs")
        plt.grid(True)
        plt.savefig(path.join(plotdir, "streaming_speeds.pdf"))
        plt.close()
