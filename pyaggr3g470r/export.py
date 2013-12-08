#! /usr/bin/env python
#-*- coding: utf-8 -*-

# pyAggr3g470r - A Web based news aggregator.
# Copyright (C) 2010-2013  Cédric Bonhomme - http://cedricbonhomme.org/
#
# For more information : http://bitbucket.org/cedricbonhomme/pyaggr3g470r/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

__author__ = "Cedric Bonhomme"
__version__ = "$Revision: 0.5 $"
__date__ = "$Date: 2011/10/24 $"
__revision__ = "$Date: 2013/12/07 $"
__copyright__ = "Copyright (c) Cedric Bonhomme"
__license__ = "GPLv3"

#
# This file contains the export functions of pyAggr3g470r. Indeed
# it is possible to export the database of articles in different formats:
# - simple HTML webzine;
# - text file.
#

import os
import time
import tarfile

import conf
import utils
import models

def HTML_HEADER(title="pyAggr3g470r", css="./style.css"):
    return """<!DOCTYPE html>
<html lang="en-US">
<head>
<title>%s</title>
<meta charset="utf-8"/>
<link rel="stylesheet" href="%s" />
</head>
<body>""" % (title, css)

HTML_FOOTER = """<hr />
<p>This archive has been generated with
<a href="https://bitbucket.org/cedricbonhomme/pyaggr3g470r/">pyAggr3g470r</a>.
A software under GPLv3 license.
You are welcome to copy, modify or redistribute the source code according to the
<a href="http://www.gnu.org/licenses/gpl-3.0.txt">GPLv3</a> license.</p>
</body>
</html>
"""

CSS = """body {
    font:normal medium 'Gill Sans','Gill Sans MT',Verdana,sans-serif;
    margin:1.20em auto;
    width:80%;
    line-height:1.75;
}
blockquote {
    font-size:small;
    line-height:2.153846;
    margin:2.153846em 0;
    padding:0;font-style:oblique;
    border-left:1px dotted;
    margin-left:2.153846em;
    padding-left:2.153846em;
}
blockquote p{
    margin:2.153846em 0;
}
p+br {
    display:none;
}
h1 {
font-size:large;
}
h2,h3 {
    font-size:medium;
}
hr {
    border-style:dotted;
    height:1px;
    border-width: 1px 0 0 0;
    margin:1.45em 0 1.4em;
    padding:0;
}
a {
    text-decoration:none;
    color:#00008B;
}
#footer {
    clear:both;
    text-align:center;
    font-size:small;
}
img {
    border:0;
}
.horizontal,.simple li {
    margin:0;
    padding:0;
    list-style:none;
    display:inline
}
.simple li:before {
    content:"+ ";
}
.simple > li:first-child:before {
    content:"";
}
.author {
    text-decoration:none;
    display:block;
    float:right;
    margin-left:2em;
    font-size:small;
}
.content {
    margin:1.00em 1.00em;
}"""

def export_html(feeds):
    """
    Export the articles given in parameter in a simple Webzine.
    """
    nb_articles = format(len(models.Article.objects()), ",d")
    index = HTML_HEADER("News archive")
    index += "<h1>List of feeds</h1>\n"
    index += """<p>%s articles.</p>\n<ul>\n""" % (nb_articles,)
    for feed in feeds:
        # creates a folder for each stream
        feed_folder = conf.PATH + "/pyaggr3g470r/var/export/webzine/" + str(feed.oid)
        try:
            os.makedirs(feed_folder)
        except OSError:
            # directories already exists (not a problem)
            pass

        index += """    <li><a href="%s">%s</a></li>\n""" % (feed.oid, feed.title)

        posts = HTML_HEADER(feed.title, "../style.css")
        posts += """<h1>Articles of the feed <a href="%s">%s</a></h1>\n""" % (feed.site_link, feed.title)
        posts += """<p>%s articles.</p>\n""" % (format(len(feed.articles), ",d"),)

        for article in feed.articles:

            post_file_name = os.path.normpath(feed_folder + "/" + str(article.id) + ".html")
            feed_index = os.path.normpath(feed_folder + "/index.html")

            posts += article.date.ctime() + " - " + """<a href="./%s.html">%s</a>""" % \
                                                            (article.id, article.title[:150]) + "<br />\n"

            a_post = HTML_HEADER(article.title, "../style.css")
            a_post += '<div style="width:60%; overflow:hidden; text-align:justify; margin:0 auto">\n'
            a_post += """<h1><a href="%s">%s</a></h1>\n<br />""" % \
                        (article.link, article.title)
            a_post += article.content
            a_post += "</div>\n<hr />\n"
            a_post += """<br />\n<a href="%s">Complete story</a>\n<br />\n""" % (article.link,)
            a_post += HTML_FOOTER

            with open(post_file_name, "w") as f:
                f.write(a_post.encode("utf-8"))

        posts +=  HTML_FOOTER
        with open(feed_index, "w") as f:
            f.write(posts.encode("utf-8"))

    index += "</ul>\n"
    index += "<p>" + time.strftime("Generated on %d %b %Y at %H:%M.") + "</p>\n"
    index += HTML_FOOTER
    with open(conf.PATH + "/pyaggr3g470r/var/export/webzine/" + "index.html", "w") as f:
        f.write(index.encode("utf-8"))
    with open(conf.PATH + "/pyaggr3g470r/var/export/webzine/" + "style.css", "w") as f:
        f.write(CSS.encode("utf-8"))

    with tarfile.open(conf.PATH + "/pyaggr3g470r/var/export.tar.gz", "w:gz") as tar:
        tar.add(conf.PATH + "/pyaggr3g470r/var/export/webzine/", arcname=os.path.basename(conf.PATH + "/pyaggr3g470r/var/export/webzine/"))

def export_txt(mongo_db):
    """
    Export the articles given in parameter in text files.
    """
    feeds = mongo_db.get_all_feeds()
    for feed in feeds:
        # creates folder for each stream
        folder = conf.PATH + "/var/export/txt/" + \
                utils.normalize_filename(feed["feed_title"].strip().replace(':', '').lower())
        try:
            os.makedirs(folder)
        except OSError:
            # directories already exists (not a problem)
            pass

        for article in mongo_db.get_articles(feed_id=feed["feed_id"]):
            name = article["article_date"].ctime().strip().replace(' ', '_')
            name = os.path.normpath(folder + "/" + name + ".txt")

            content = "Title: " + article["article_title"] + "\n\n\n"
            content += utils.clear_string(article["article_content"])

            with open(name, "w") as f:
                f.write(content)