scbulletin2.py
==============

This is an alternative version of scbulletin. A partial rewrite and
cleanup. For the time being in order not to mess up the scbulletin
shipped as part of SeisComP, I maintain it here so you can play
around with it.

The main advantages include:

- Clear separation of input and output

- An EventParameters instance is read from database, XML or whereever

- The Bulletin class is only a formatter and doesn't require any database access. It is only passed the EventParameters instance

- More conveniently accessible from any Python script

Nevertheless, this is still work in progress. Suggestions and ideas
for improvements are highly appreciated.
