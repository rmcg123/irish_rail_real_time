"""Configuration file for real time trains work."""

IRISH_RAIL_API_BASE = "http://api.irishrail.ie/realtime/"

IRISH_RAIL_REAL_TIME_TRAINS = (
    IRISH_RAIL_API_BASE + "realtime.asmx/getCurrentTrainsXML"
)

IRELAND_MAPS_OUTPUT = "results/ireland/"
IRELAND_CENTRE_POINT = [53.4494762, -7.5029786]

DUBLIN_MAPS_OUTPUT = "results/dublin/"
DUBLIN_CENTRE_POINT = [53.350140, -6.266155]

CORK_MAPS_OUTPUT = "results/cork/"
CORK_CENTRE_POINT = [51.903614, -8.468399]
