#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name = "scstuff",
    version = "0.5.0",
    author = "Joachim Saul",
    author_email = "saul@gfz-potsdam.de",
    packages = ['scstuff'],

    package_data = {
        'scstuff' : [
            "__init__.py",
            "util.py",
            "dbutil.py",
            "mtutil.py",
            "bulletin.py",
            "inventory",
            "eventclient.py",
            "eventloader.py"
        ]
    },

    scripts = [
        "apps/xml/scstuff.xml-dump-with-mt.py",
        "apps/xml/scstuff.xml-anonymize.py",
        "apps/xml/scstuff.xml-to-mt-txt.py",
        "apps/teleseismic-traveltimes/scstuff.ttt.py",
        "apps/set-magnitude-type/scstuff.set-magtype.py",
        "apps/inv-to-sacpz/scstuff.inv-to-sacpz.py",
        "apps/station-coordinates-to-inventory/scstuff.make-mini-inventory.py",
        "playback/xml/scstuff.playback-dump-picks.py"
    ]
)
