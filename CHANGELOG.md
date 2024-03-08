# Unreleased

- scraper will fail when there are too many errors while retrieving xblocks
- move all inline Javascript to standalone files to comply with some CSP
- no more retry for login + HTTP errors
- display HTTP error responses or save them in a temporary file for analysis
- save API response for course xblocks in temporary file for debugging
- pin markupsafe until we upgrade Jinja2
- fix issue with video that do not need to be re-encoded and were marked as missing
- README.md: replace course in sample command by one under a Creative Commons license

# 1.0.2

- changed default publisher metadata from 'Kiwix' to 'openZIM'

# 1.0.1

- fixed recursive paths and URLs in html_processor.py
- fixed usage on older browsers (without ES6 support)
- added multithreading support
- fixed missing videos due to youtube_dl error
- added support for convertion in high quality
- use dynamic versions for opensans font
- fixed mobile navigation menu
- fixed video encoding in low quality in WebM
- added support for internationalization
- have proper language in ZIM metadata
- updated zimscraperlib

# 1.0.0

- new structure for the project
- using fixed version of dependencies
- wiki and forums now optional
- using zimscraperlib for downloading and optimizing videos
- refactored Dockerfile
- added s3 based optimization cache
- removed javascript dependencies from repository
- added support for webm on systems without native support
- fixed small favicons
- using pylibzim for creating ZIMs
- fixed internal links
- using params instead of instance configs
- using course layout from instance
- added videojs based audio player to solve compatibility issues
- fixed problem answer fetching
