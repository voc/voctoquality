from libquality.profile import Profile as Base


class Profile(Base):
    """Example profile for testing and demonstration"""
    name = "simple"
    dimensions = ["codec"]

    def formats(self):
        """Returns formats to encode"""
        for codec in ["copy", "libvpx-vp9", "libx264", "libx265"]:
            yield {
                "codec": codec,
                "opts": f"-i $ref -c:v {codec}"
            }

    def plot(self, df, plotdir):
        """Plots scores and stores them in plotdir"""
        df.plot()
