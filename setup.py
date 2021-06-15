#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name = "scstuff",
    version = "0.2.0",
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
            "eventloader.py"
        ]
    },

    scripts = [
        "apps/scbulletin2.py",
        "apps/xml/scstuff.xml-dump-with-mt.py",
        "apps/xml/scstuff.xml-anonymize.py",
        "apps/xml/scstuff.xml-to-mt-txt.py",
        "apps/teleseismic-traveltimes/scstuff.ttt.py",
        "apps/set-magnitude-type/scstuff.set-magtype.py"
    ]
)
