# `scstuff.set-magtype.py`

This utility sets the preferred magnitude type for an event. It
works via messaging, allowing all connected clients to be notified
of the change. Direct modification of the database is not
possible. The utility includes support for moment magnitude Mw.

### Example

To set the magnitude type of event gfz2019abcd to "Mw", invoke

```
server=...
event=gfz2019abcd

seiscomp-python scstuff.set-magtype.py -H $server -u "" --event $event --magnitude-type Mw
```
