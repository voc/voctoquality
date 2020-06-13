import json
import glob
from os import path, makedirs
from libquality import ffmpeg

def compare(references, profiles, tag, env):
    for profile in profiles:
        # store scores per profile
        scores = []
        scorefile = path.join(env["scoredir"], f"{tag}_{profile.name}.json")

        makedirs(env["scoredir"], exist_ok=True)

        print(f"Processing profile: {profile.name}")
        for reference in references:
            print(f"Processing reference: {reference}")
            for result in profile.process(reference, tag, env["tmpdir"]):
                scores.append(result)

                # dump after every result to preserve work
                with open(scorefile, "w") as f:
                    json.dump(scores, f, indent="  ")

def plot(profiles, env):
    import pandas as pd
    scores = []

    # load all scores for plotting
    files = glob.iglob(path.join(env["scoredir"], "*.json"))
    for filename in files:
        with open(filename, "r") as f:
            scores += json.load(f)

    df = pd.DataFrame(scores)
    for profile in profiles:
        profile.plot(df.loc[lambda df: df["profile"] == profile.name, :].copy())