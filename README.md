# fb_CollectPostsComments
This is a python3 script that allows to collect posts and comments from Facebook pages. It requires the following packages:

- facebook (should be the latest version. Install from github)
- requests
- os.path
- sys
- time
- sqlite3
- datetime
- configparser
- re

To run this, Facebook API credentials and a date until when posts should be collected, must be defined in the config file. Posts and comments can then be collected either:

- from single pages by setting the page name in the config file and running `fb_singleCollect.py`
- from multiple pages by providing a comma separated list of page names in `data/__input` and running `fb_singleCollect.py`

The script will store posts and comments in a single sqlite database for each page.
Note that the Facebook API eventually throws errors that are not handled in these scripts. However, when running the script again it will continue collecting from where it failed. If not, delete the database manually and start again.  
