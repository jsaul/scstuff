scstuff.inv2sacpz
=================

This is a small utilily that retrieves sensor information from a
SeisComP inventory and dumps the poles and zeros in `sacpz` format.

The main purpose is of course to retrieve poles and zeros to be used
in waveform restitution (instrument deconvolution). But it can also
be useful for interfacing SeisComP and non-SeisComP (e.g. SAC or
ObsPy based) modules. In addition to the actual poles and zeros
information, the output alsp contains additional station metadata
via comments, similar to the `sacpz` format of rdseed and IRIS's
`sacpz` webservice. This makes it a convenient tool for
visualization and debugging of SeisComP station inventories.

```
  scstuff.inv-to-sacpz.py --debug -d "$db" -C
```

will dump all configured and currently active streams to sacpz files
in the current directory; one file per stream.
