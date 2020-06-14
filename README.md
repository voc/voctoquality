# FFmpeg video setting comparison framework
[![build and test](https://github.com/voc/voctoquality/workflows/build%20and%20test/badge.svg)](https://github.com/voc/voctoquality/actions)
[![codecov](https://codecov.io/gh/voc/voctoquality/branch/master/graph/badge.svg)](https://codecov.io/gh/voc/voctoquality)

Python framework for comparing video encoding quality for different ffmpeg settings. Automates the whole process of preparing reference files, encoding, scoring, and plotting.

Comparisons are run in docker with ffmpeg and libvmaf, vaapi, libvpx, libx264 and libx265 support.

## Why is this useful?
When trying to encode video content you currently have a gigantic ecosystem of different software and hardware-encoders available at your disposal and each of them comes with a large number of confusing knobs to tweak. Depending on your goals the default settings might do a fine job, but to understand how a specific setting influences encoding quality and speed it can be very useful to be able to objectively compare the results.

Companies like netflix have to deal with these problems every day and that's why they developed the [Video Multimethod Assessment Fusion (VMAF)](https://netflixtechblog.com/toward-a-practical-perceptual-video-quality-metric-653f208b9652) metric and [open-sourced it in 2016](https://github.com/Netflix/vmaf.git).

This metric takes a reference video file and a distorted (encoded) video file and produces a score of 0-100

## Limitations
While the VMAF-metric is very good it's also not a replacement for the human eye. To give you an idea, here's a list of things to keep in mind while using it:
  - **Time**: VMAF doesn't take temporal effects into account, as it "only" aggregates per-frame metrics. So videos with problems like duplicate frames and jitter might still produce high scores. It is recommended to take a look at some of the encoded files manually to make sure the scores are reasonable.
  - **Context**: The scores depend on the data the VMAF model was trained with so the scores can differ from real-world testing for different content and different viewing conditions (screen size, viewing distance, lighting, display resolution, frame rate). [The default model was trained for 1080p content with TV viewing conditions](https://github.com/Netflix/vmaf/blob/master/FAQ.md).
  - **Aggregation matters**: an arithmetic mean of all per-frame scores might be too optimistic in the presence of low-score outliers. For this reason different aggregate scoring methods should be used to get an idea of the range of values.
  - **Machine Learning**: The VMAF metric is actually an aggregation of multiple common video quality metrics such as PSNR and SSIM using a support vector machine (SVM). As such the absolute scores might not always be constrained to the range [0, 100] and comparing a reference video with itself might not yield a perfect score of 100.

## Difference to other vmaf-containers
This repository is intended for semi-automated exploration and testing of different encoding settings. If you just want a minimal container that can provide you a VMAF-score you are probably better off with one of the following projects:
  - https://github.com/leandromoreira/docker-ffmpeg-vmaf
  - https://github.com/sitkevij/vmaf

## How to use this
Start off by cloning this repository to your machine
```bash
git clone https://github.com/voc/voctoquality.git
cd voctoquality
```

### Preparing the environment
First we need to setup our standardized test environment inside docker

**Either use the prebuilt container from docker hub**
```bash
# this will just start a bash inside the container with your vaapi-device mounted if you have one
./run.sh
```

**Or build the container yourself**
```bash
docker build --tag voctoquality .
docker run \
  --rm \
  --privileged \
  -v /dev/dri:/dev/dri \
  -v `pwd`:/root \
  -it voctoquality /bin/bash
```

In our container environment we now have all required libraries present to run reproducible quality comparisons.

### Running quality comparisons
Make sure your shell is running inside the container.

#### Running comparisons
Now you can run the standard comparisons included in the library you must specify a tag to identify your hardware environment this will be stored alongside your computed scores and used as label in plots
```bash
./compute_quality.py skylake
```

#### What's going on
Now this will do a number of things, namely:
  - download video sources and prepare them as reference files as specified in sources.json
    - all references are checked against md5-hashes if those are present in sources.json
    - a custom source list can be used using *--source mysources.json*
  - encode all references to all formats specified in the selected comparison profiles
    - all encoded files are put into the *./tmp* directory
  - compute scores for all encoded files
    - the scores are stored in the *./scores* directory
  - create plots using those scores

#### More examples
```bash
# List available comparisons and options
./compute_quality.py -h

# Run a specific comparison profile
./compute_quality.py --profile voc-streaming skylake

# Just create plots without encoding anything
# This is useful if you want to show scores from different environments together in a single plot
# Just place the scores-files from these environments in your local ./scores directory
./compute_quality.py -t plot
```
