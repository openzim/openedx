# openedx2zim

##### Get the best courses :books: powered by openedx offline :arrow_down:
An offliner to create ZIM :package: files from openedx powered courses

[![PyPI](https://img.shields.io/pypi/v/openedx2zim?style=for-the-badge)](https://pypi.org/project/openedx2zim/)
[![Docker](https://img.shields.io/docker/build/openzim/openedx?style=for-the-badge)](https://hub.docker.com/r/openzim/openedx)
[![Codefactor Grade](https://img.shields.io/codefactor/grade/github/openzim/openedx/master?label=codefactor&style=for-the-badge)](https://www.codefactor.io/repository/github/openzim/openedx)
[![License](https://img.shields.io/github/license/openzim/openedx?color=blueviolet&style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)

Openedx is one of the most popular open source MOOC platforms which revolves around the idea of xblocks. It makes e-learning more accessible by providing an easy way to create courses for teachers, universities and others. It is used by many e-learning services as such as edX as a tool to create, organize and manage MOOCs quite easily.

This project is aimed at creating a tool to make openedx based MOOCs more accessible by creating ZIM files providing the same course materials and resources offline.


## Getting started :rocket:

#### Install the dependencies
Make sure that you have `python3`, `unzip`, `ffmpeg`, `wget`, `jpegoptim`, `gifsicle`, `pngquant`, `advdef`, and `curl` installed on your system before running the scraper (otherwise you'll get a warning to install them).

#### Enroll into the MOOC
You must be enrolled into the mooc you want to offline. Ensure that you do not open the openedx instance in the browser with the same account while the scraper runs. Also, this scraper must be used only with a MOOC with a free license. 

#### Setup the package
One can eaisly install the PyPI version but let's setup the source version. Firstly, clone this repository and install the package as given below.

```bash
pip3 install -r requirements.txt
```

```bash
python3 setup.py install
```

That's it. You can now run `openedx2zim` from your terminal

```bash
openedx2zim --course-url [URL] --email [EMAIL] --name [NAME]
```

For the full list of arguments, see [this](openedx2zim/entrypoint.py) file or run the following
```bash
openedx2zim --help
```

Example usage
```bash
openedx2zim --course-url="https://courses.edx.org/courses/course-v1:edX+edx201+1T2020/course/" --publisher="edx201" --email="example@example.com" --name="sample" --tmp-dir="output" --output="output" --debug  --keep --format="mp4"
```

This project can also be run with docker. Use the provided [Dockerfile](Dockerfile) to run it with docker. See steps [here](https://docs.docker.com/get-started/part2/).

## Features :robot:
You can create ZIMs for MOOCs powered by the openedx platform (find a list of openedx powered instances [here](https://openedx.atlassian.net/wiki/spaces/COMM/pages/162245773/Sites+powered+by+Open+edX+Platform)), choose between different video formats (webm/mp4), different compression rates, and even use an S3 based cache.

## Limitations :exclamation:
The answers can be extracted only for "multiple choice question" type problems with single answer correct and multiple answer correct (only if the number of options in that case is at most 5). This is due to large number of requests required to extract answers for other types of answers. For more information, refer [here](https://github.com/openzim/openedx/issues/35).

## License :book:

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.
