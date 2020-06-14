from libquality.profile import Profile as Base


class Profile(Base):
    name = "simple"
    dimensions = ["codec"]

    def formats(self):
        for codec in ["copy", "libvpx-vp9", "libx264", "libx265"]:
            yield {
                "codec": codec,
                "opts": f"-i $ref -c:v {codec}"
            }

    def plot(self, df, plotdir):
        df.plot()
