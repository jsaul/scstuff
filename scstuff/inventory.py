# -*- coding: utf-8 -*-

def operational(obj, time):
    """
    Return True if the inventory item 'obj' is considered
    operational at the specified time. False is returned otherwise.
    """
    # If the start time of an inventory item is not
    # known, it is not considered operational.
    try:
        start = obj.start()
        assert time >= start
    except:
        return False

    # If the end time of an inventory item is not
    # known it is considered "open end".
    try:
        end = obj.end()
        if time > end:
            return False
    except:
        pass

    return True


def InventoryIterator(inventory, time=None):
    """
    inventory is a SeisComP inventory instance
    """

    for inet in range(inventory.networkCount()):
        network = inventory.network(inet)
        if time is not None and not operational(time, network):
            continue

        for ista in range(network.stationCount()):
            station = network.station(ista)

            if time is not None and not operational(time, station):
                continue

            for iloc in range(station.sensorLocationCount()):
                location = station.sensorLocation(iloc)

                if time is not None and not operational(time, location):
                    continue

                for istr in range(location.streamCount()):
                    stream = location.stream(istr)

                    if time is not None and not operational(time, stream):
                        continue

                    yield network, station, location, stream

