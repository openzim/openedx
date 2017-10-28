
# openedx2zim

*openedx to Kiwix*

The goal of this project is to create a suite of tools to create [zim](http://www.openzim.org) files required by [kiwix](http://kiwix.org/) reader to make available Massive Open Online Courses (MOOCs) from [any OpenEdx instance](https://openedx.atlassian.net/wiki/spaces/COMM/pages/162245773/Sites+powered+by+Open+edX) offline (without access to Internet).


## Getting started

Install non python dependencies:

Here for Debian : 
```
sudo apt-get install jpegoptim pngquant gifsicle advancecomp python-pip python-virtualenv python-dev imagemagick ffmpeg
```

Create a virtual environment for python:

```
virtualenv -p python3 venv
```

Activate the virtual enviroment:

```
source venv/bin/activate
```


Install this lib:

```
pip install openedx2zim
```

##Usage

```
openedx2zim <course_url> <publisher> <email> [--password=<pass>] [--nozim] [--zimpath=<zimpath>] [--nofulltextindex]
```

course_url is something like this https://courses.edx.org/courses/[course name or id]/info you can find it from your dashboard and click on the MOOC you want to offline
You should already have enrolled course to make it offline.
Also you should not connect on your browser or with an other run of openedx2zim to the same account while openedx2zim is still running.


You should only use this to MOOC with a free licence.




