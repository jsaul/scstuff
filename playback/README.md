playbacks
=========

*Scripts to support playbacks in SeisComP 3*

There are many different objectives for doing playbacks and
therefore different mechanisms that can be used.

* Full waveform playback

  Waveform playbacks innvolve the processing of a data time window
that can range in length from just minutes to years. Short playbacks
are usually made for testing (incl. stress tests) or demo purposes.
Long playbacks are used for offline processing of large quantities
of waveforms. This is typically the case after a seismological field
experiment has been finalized and the waveform data shall be
analyzed for local seismicity.


* Parameter-only playback

  Waveform playbacks are relatively "heavy" as the full waveform
processing requires a lot of system resources. In some cases,
especially for testing and debugging, much lighter parameter-only
playbacks are preferred because they are much easier to run ad hoc
and repeatedly. This kind of playback is particularly useful for
modules like scautoloc, which doesn't process waveforms directly.
Instead it only processes picks and amplitudes previously measured
by a picker like scautopick. Both picks and amplitudes are usually
static. This means that they are determined once and are unlikely to
change later on. Therefore we can retrieve these objects from the
database and simulate the real-time processing by using the object
creation time to reproduce (and possibly debug) the real-time
behaviour. This works by reading the picks and amplitudes from an
XML file, sorting them according to their creation times and
playing them back in that order.

  This kind of parametric playback is very easy to generate from the
database. In fact it could even be generated from the database on
the fly. It will work to play back amplitudes, picks and even
origins, but only as long as they can be assumed to be static.
Other object types like events and network magnitudes get updated
during the processing and therefore cannot be played back properly.
This is because the final state of these objects in the database can
of course not reflect their evolution. Overwriting them in the
database means loss of information about their previous state!

  A much more complete history of an event can be captured by
logging also the transient state of objects in the form of notifier
messages. Support for this may be added to SeisComP in future.
Some proof-of-concept Python scripts to demonstrate the power of
this playback mechanism are included here already.  The idea is to
subscribe to all relevant messaging groups and grab all notifier
messages that come around.  Each received notifier message is saved
as XML document to a notifier log. Each log entry is preceded by a
header line containing a time stamp for synchonization and the
length of the following XML document in bytes. This log will have to
be run continuously and stored e.g. in day files.



Content:

* mseed/

    generation of sorted, multiplexed MiniSEED files suitable for
    full waveform playback in SeisComP 3

* xml/

    XML based parameter playback (mainly for picks/amplitudes)
    primarily for testing and debugging of scautoloc

* notifier/

    XML based parameter playbacks using notifier logs. Highly
    experimental

