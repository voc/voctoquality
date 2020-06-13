import libquality.ffmpeg as ffmpeg
import os.path as path


class InvalidEncodingFormat(Exception):
    pass


class Profile:
    """Comparison Profile, contains encoding formats and plots for comparison"""

    def __init__(self, name, formats, plots, scale=None):
        """
        Creates a new comparison profile with encoding formats and plotting formats

        | Arguments:
        | formats: dict with encoding formats
        | plots: list of plotting functions
        """
        self.name = name
        self.format = formats
        self.plots = plots
        self.scale = scale

        self.aggregations = ["harm_mean", "10th_pct", "min"]
        self.aggregationLabels = ["Harmonic Mean", "10th Percentile", "Minimum"]

    def process(self, reference, tag, tmpdir):
        """
        Compute scores for a reference with all formats in this profile
        """
        count = 0

        rawref = path.join(tmpdir, "ref.nut")
        ffmpeg.decode(reference, rawref)
        formats = self.format.formats
        for fmt in formats:
            refname = path.basename(path.splitext(reference)[0])
            desc = self.format.get_descriptor(fmt, refname, self.name, tag)
            try:
                result = ffmpeg.transcode(rawref, desc, fmt["opts"], self.scale, tmpdir=tmpdir)
                yield self.format.annotate_result(result, fmt, refname, self.name, tag)
            except (ffmpeg.EncodeFailed, ffmpeg.ScoreFailed) as err:
                print(err)
            count += 1
            print(f"{count}/{len(formats)} formats complete ({(count/len(formats)*100):0.2f}%)")

    def plot(self, df):
        for plotfn in self.plots:
            plotfn(df.copy())

class EncodingFormats:
    def __init__(self, dimensions, formats):
        """
        | Arguments:
        | dimensions: list of format key dimensions
        | formats: iterable of encoding formats
        """

        # add custom dimensions to base dimensions
        self.dimensions = ["tag", "profile", "reference"] + dimensions
        self.formats = self.process_formats(dimensions, formats)

    def annotate_result(self, result, fmt, reference, profile, tag):
        values = {**{
            "reference": reference,
            "profile": profile,
            "tag": tag,
        }, **fmt, **result}

        return values

    def get_descriptor(self, fmt, reference, profile, tag=""):
        # generate unique format descriptor
        descriptor = []
        values = {**{
            "reference": reference,
            "profile": profile,
            "tag": tag,
        }, **fmt}

        for dim in self.dimensions:
            descriptor.append(str(values[dim]))

        return "_".join(descriptor)

    def process_formats(self, dimensions, formats):
        result = []
        for fmt in formats:
            # check if all custom dimensions are present
            for dimension in dimensions:
                if dimension not in fmt:
                    raise InvalidEncodingFormat(f"Value for {dimension} not present in format {fmt}")

            # check if encoding opts are present
            if "opts" not in fmt:
                raise InvalidEncodingFormat(f"Encoding options not present in format {fmt}")

            result.append(fmt)

        return result



