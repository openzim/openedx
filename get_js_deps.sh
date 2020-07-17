#!/bin/sh

###
# download JS dependencies and place them in our templates/assets folder
# then launch our ogv.js script to fix dynamic loading links
###

if ! command -v curl > /dev/null; then
	echo "you need curl."
	exit 1
fi

if ! command -v unzip > /dev/null; then
	echo "you need unzip."
	exit 1
fi

# Absolute path this script is in.
SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
ASSETS_PATH="${SCRIPT_PATH}/openedx2zim/templates/assets"

echo "About to download JS assets to ${ASSETS_PATH}"

echo "getting open sans font"
curl -L -o opensans.zip http://google-webfonts-helper.herokuapp.com/api/fonts/open-sans?download=zip\&subsets=vietnamese,latin-ext,latin,greek-ext,greek,cyrillic-ext,cyrillic\&variants=regular\&formats=woff,woff2
rm -rf $ASSETS_PATH/fonts/opensans
mkdir -p $ASSETS_PATH/fonts/opensans
unzip -o -d $ASSETS_PATH/fonts/opensans opensans.zip
rm -f opensans.zip

echo "getting fontawesome"
curl -L -O https://use.fontawesome.com/releases/v5.13.1/fontawesome-free-5.13.1-web.zip
rm -rf $ASSETS_PATH/fontawesome
unzip -o -d $ASSETS_PATH fontawesome-free-5.13.1-web.zip
mv $ASSETS_PATH/fontawesome-free-5.13.1-web $ASSETS_PATH/fontawesome
rm -rf $ASSETS_PATH/fontawesome/js $ASSETS_PATH/fontawesome/less $ASSETS_PATH/fontawesome/metadata $ASSETS_PATH/fontawesome/scss $ASSETS_PATH/fontawesome/sprites $ASSETS_PATH/fontawesome/svgs $ASSETS_PATH/fontawesome/LICENSE.txt
rm -f fontawesome-free-5.13.1-web.zip

echo "getting video.js"
curl -L -O https://github.com/videojs/video.js/releases/download/v7.8.1/video-js-7.8.1.zip
rm -rf $ASSETS_PATH/videojs
mkdir -p $ASSETS_PATH/videojs
unzip -o -d $ASSETS_PATH/videojs video-js-7.8.1.zip
rm -rf $ASSETS_PATH/videojs/alt $ASSETS_PATH/videojs/examples
rm -f video-js-7.8.1.zip

echo "getting mathjax"
curl -L -O https://github.com/mathjax/MathJax/archive/3.0.5.zip
rm -rf $ASSETS_PATH/mathjax
unzip -o -d $ASSETS_PATH 3.0.5.zip
mv $ASSETS_PATH/MathJax-3.0.5/es5 $ASSETS_PATH/mathjax
rm -rf $ASSETS_PATH/MathJax-3.0.5
rm -f 3.0.5.zip

echo "getting jquery.min.js"
curl -L -o $ASSETS_PATH/jquery.min.js https://code.jquery.com/jquery-3.5.1.min.js

echo "getting ogv.js"
curl -L -O https://github.com/brion/ogv.js/releases/download/1.6.1/ogvjs-1.6.1.zip
rm -rf $ASSETS_PATH/ogvjs
unzip -o ogvjs-1.6.1.zip
mv ogvjs-1.6.1 $ASSETS_PATH/ogvjs
rm -f ogvjs-1.6.1.zip

echo "getting videojs-ogvjs.js"
curl -L -O https://github.com/hartman/videojs-ogvjs/archive/v1.3.1.zip
rm -f $ASSETS_PATH/videojs-ogvjs.js
unzip -o v1.3.1.zip
mv videojs-ogvjs-1.3.1/dist/videojs-ogvjs.js $ASSETS_PATH/videojs-ogvjs.js
rm -rf videojs-ogvjs-1.3.1
rm -f v1.3.1.zip

if command -v fix_ogvjs_dist > /dev/null; then
    echo "fixing JS files"
    fix_ogvjs_dist $ASSETS_PATH "assets"
else
    echo "NOT fixing JS files (zimscraperlib not installed)"
fi