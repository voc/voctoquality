import libquality.ffmpeg as ffmpeg
from os import path, makedirs


class InvalidEncodingFormat(Exception):
    pass


class Profile:
    """
    Comparison Profile, contains encoding formats and plots for comparison
    """
    name = None
    scale = None
    dimensions = []

    # Override
    def formats(self):
        pass

    # Override
    def plot(self, df):
        pass

    def get_dimensions(self):
        # add custom dimensions to base dimensions
        return ["tag", "profile", "reference"] + self.dimensions

    def get_formats(self):
        result = []
        for fmt in self.formats():
            if fmt is None:
                continue

            # check if all custom dimensions are present
            for dimension in self.dimensions:
                if dimension not in fmt:
                    raise InvalidEncodingFormat(f"Value for '{dimension}' not in format {fmt}")

            # check if encoding opts are present
            if "opts" not in fmt:
                raise InvalidEncodingFormat(f"Encoding 'opts' not in format {fmt}")

            result.append(fmt)

        return result

    def get_descriptor(self, fmt, reference, tag):
        """Generates a unique descriptor for an encoding"""
        descriptor = []
        values = {**{
            "reference": reference,
            "profile": self.name,
            "tag": tag,
        }, **fmt}

        for dim in self.get_dimensions():
            descriptor.append(str(values[dim]))

        return "_".join(descriptor)

    def annotate_result(self, result, fmt, reference, tag):
        """Adds profile metadata to result scores"""
        values = {**{
            "reference": reference,
            "profile": self.name,
            "tag": tag,
        }, **fmt, **result}

        return values

    def process(self, reference, tag, tmpdir):
        """
        Compute scores from a reference for all formats in this profile
        """
        count = 0

        # decode reference
        makedirs(tmpdir, exist_ok=True)
        rawref = path.join(tmpdir, "ref.nut")
        ffmpeg.decode(reference, rawref)

        formats = self.get_formats()
        for fmt in formats:
            refname = path.basename(path.splitext(reference)[0])
            desc = self.get_descriptor(fmt, refname, tag)

            try:
                result = ffmpeg.transcode(rawref, desc, fmt["opts"], self.scale, tmpdir=tmpdir)
                yield self.annotate_result(result, fmt, refname, tag)

            except (ffmpeg.EncodeFailed, ffmpeg.ScoreFailed) as err:
                print(err)

            count += 1
            percentage = count / len(formats) * 100
            print(f"{count}/{len(formats)} formats complete ({percentage:0.2f}%)")
