
# openedx2zim

*openedx to Kiwix*

The goal of this project is to create a suite of tools to create [zim](http://www.openzim.org) files required by [kiwix](http://kiwix.org/) reader to make available mooc from any OpenEdx instance offline (without access to Internet).


Currently we only support edx.org

## Getting started

Install non python dependencies:

```
sudo apt-get install jpegoptim pngquant gifsicle advancecomp python-pip python-virtualenv python-dev imagemagick
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
openedx2zim <course_url> <publisher> <email> [--password=<pass>] [--nozim] [--zimpath=<zimpath>]
```

course_url is something like this https://courses.edx.org/courses/[course name/id]/info you can find it from your dashboard and click on the mooc you want to offline
You should already have enrolled course to make it offline.

You should only use this to mooc with a free licence.




