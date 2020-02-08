#!/usr/bin/env python3

PICKUP_TIME_LIMIT = 15
TRAVEL_TIME_RATIO_LIMIT = 1.5 # 50% longer than direct trip

from model import Trip, StopType, Stop, Node, Tour
from log import Logger


class TourGenerator:

    def __init__(self, stop_times, vehicle_2_stops_times, trips, logger_verbosity):
        self._logger = Logger(logger_verbosity)
        self._times = dict(stop_times, **vehicle_2_stops_times)
        self._trip_by_id = dict(map(lambda t: (t.id, t), trips))
        trip_to_stop_list = lambda t: [Stop(t.pickup_stop_id, t.id, StopType.PICKUP),
                                       Stop(t.dropoff_stop_id, t.id, StopType.DROPOFF)]
        self._stops = [stop
            for stop_list in map(trip_to_stop_list, trips)
                for stop in stop_list]
        self._logger(3, 'Initialized with:')
        self._logger(3, 'times:', self._times)
        self._logger(3, 'trips_by_id:', self._trip_by_id)
        self._logger(3, 'stops:', self._stops)

    def tours(self, vehicle_id):
        empty_tour = Tour(
            vehicle_id=vehicle_id,
            path='',
            nodes=(),
            picked_up_trip_ids_2_nodes={},
            dropped_off_trip_ids=set(),
            total_time=0
        )
        return self._tours_recursive(vehicle_id, self._stops, empty_tour)

    def _tours_recursive(self, vehicle_id, stops, tour):
        self._logger.indent()
        nodes = tour.nodes
        if not nodes:
            # initial, empty tour, means the car doesn't have to do anything as
            # other cars take over all trips, which is a valid option
            self._logger(1, 'Empty tour')
            yield tour
        # each iteration uses one element + recursively the list minus the element
        for i, stop in enumerate(stops):
            self._logger(1, 'Next stop:', stop)
            accumulated_time = self._accumulated_time(vehicle_id, nodes, stop)
            node = Node(stop=stop, accumulated_time=accumulated_time)
            candidate_nodes = nodes + (node,)
            picked_up_trip_ids_2_nodes = tour.picked_up_trip_ids_2_nodes
            dropped_off_trip_ids = tour.dropped_off_trip_ids
            self._logger(1, 'Candidate nodes:', candidate_nodes)

            if stop.type == StopType.PICKUP:
                if not self._pickup_within_time_limit(accumulated_time):
                    self._logger(1, 'Rejected (pickup time limit)')
                    self._logger(1, 'Tour can never be valid, cutting short')
                    continue
                self._logger(1, 'Adding node:', node, 'to pickup nodes')
                picked_up_trip_ids_2_nodes = dict(picked_up_trip_ids_2_nodes, **{stop.trip_id: node})

            else:
                assert stop.type == StopType.DROPOFF

                if not self._dropoff_has_pickup(candidate_nodes, picked_up_trip_ids_2_nodes):
                    self._logger(1, 'Rejected (dropoff without pickup)')
                    self._logger(1, 'Tour can never be valid, cutting short')
                    continue

                if not self._travel_time_within_time_limit(candidate_nodes, picked_up_trip_ids_2_nodes):
                    self._logger(1, 'Rejected (travel time too long)')
                    self._logger(1, 'Tour can never be valid, cutting short')
                    continue

                self._logger(1, 'Adding node:', node, 'to dropoff nodes')
                dropped_off_trip_ids = set(dropped_off_trip_ids) | { stop.trip_id }

            valid_tour = True

            if not self._each_pickup_has_dropoff(set(picked_up_trip_ids_2_nodes.keys()), dropped_off_trip_ids):
                valid_tour = False
                self._logger(1, 'Rejected (not all pickups have a corresponding dropoff)')
                self._logger(1, 'Deeper tours may still be accepted')

            deeper_tour = Tour(
                vehicle_id=tour.vehicle_id,
                path=tour.path + ' -> ' + stop.id,
                nodes=candidate_nodes,
                picked_up_trip_ids_2_nodes=picked_up_trip_ids_2_nodes,
                dropped_off_trip_ids=dropped_off_trip_ids,
                total_time=accumulated_time
            )
            if valid_tour:
                self._logger(1, 'Accepted')
                yield deeper_tour

            sublist = stops[:]
            sublist.pop(i)
            if not sublist:
                # deepest recursion level, list exhausted
                continue
            yield from self._tours_recursive(vehicle_id, sublist, deeper_tour)
        self._logger.unindent()

    def _accumulated_time(self, vehicle_id, nodes, stop):
        self._logger(2, 'Calculating accumulated time to stop:', stop, 'with previous nodes:', nodes)
        if len(nodes):
            from_node = nodes[-1]
            self._logger(3, 'Using previous node:', from_node, 'as from')
            time = self._times[from_node.stop.id][stop.id]
            self._logger(3, 'Time from:', from_node, 'to:', stop, 'is:', time)
            accumulated_time = from_node.accumulated_time + time
        else:
            self._logger(3, 'First node, using vehicle:', vehicle_id, 'as from')
            time = self._times[vehicle_id][stop.id]
            self._logger(3, 'Time from vehicle:', vehicle_id, 'to:', stop, 'is:', time)
            accumulated_time = time
        self._logger(2, 'Accumulated time:', accumulated_time)
        return accumulated_time

    def _pickup_within_time_limit(self, pickup_accumulated_time):
        # condition 1
        self._logger(2, 'Is pickup within time limit?')
        valid = pickup_accumulated_time <= PICKUP_TIME_LIMIT
        self._logger(2, 'Pickup time:', pickup_accumulated_time, 'limit:', PICKUP_TIME_LIMIT)
        self._logger(2, 'Passed' if valid else 'Failed')
        return valid

    def _dropoff_has_pickup(self, nodes, pickup_trip_ids_2_nodes):
        # this function is only ever called for a trailing dropoff
        self._logger(2, 'Does dropoff have a corresponding pickup?')
        dropoff_stop = nodes[-1].stop
        assert dropoff_stop.type == StopType.DROPOFF
        self._logger(3, 'Dropoff stop:', dropoff_stop)
        self._logger(3, 'Checking for pickup of trip id:', dropoff_stop.trip_id, 'in:', pickup_trip_ids_2_nodes)
        valid = dropoff_stop.trip_id in pickup_trip_ids_2_nodes
        if valid:
            self._logger(3, 'Pickup found for trip id:', dropoff_stop.trip_id)
            self._logger(2, 'Passed')
        else:
            self._logger(3, 'Pickup missing for trip id:', dropoff_stop.trip_id)
            self._logger(2, 'Failed')
        return valid

    def _travel_time_within_time_limit(self, nodes, pickup_trip_ids_2_nodes):
        # condition 2
        # this function is only ever called for a trailing dropoff
        self._logger(2, 'Is travel time within time limit?')
        dropoff_node = nodes[-1]
        dropoff_stop = dropoff_node.stop
        assert dropoff_stop.type == StopType.DROPOFF
        self._logger(3, 'Dropoff stop:', dropoff_stop)
        self._logger(3, 'Searching for pickup node of trip id:', dropoff_stop.trip_id, 'in:', pickup_trip_ids_2_nodes)
        # safe operation: we previously checked a pickup for this dropoff exists
        pickup_node = pickup_trip_ids_2_nodes[dropoff_stop.trip_id]
        self._logger(3, 'Pickup node:', pickup_node, 'dropoff_node:', dropoff_node)
        travel_time = dropoff_node.accumulated_time - pickup_node.accumulated_time
        direct_connection_travel_time = self._times[pickup_node.stop.id][dropoff_node.stop.id]
        valid = travel_time <= TRAVEL_TIME_RATIO_LIMIT * direct_connection_travel_time
        self._logger(2, 'Travel time:', travel_time, 'direct connection travel time:', direct_connection_travel_time)
        self._logger(2, 'Passed' if valid else 'Failed')
        return valid

    def _each_pickup_has_dropoff(self, picked_off_trip_ids, dropped_off_trip_ids):
        # condition 5
        self._logger(2, 'Does each pickup have a corresponding dropoff?')
        self._logger(3, 'Picked up trip ids:', picked_off_trip_ids)
        self._logger(3, 'Dropped off trip ids:', dropped_off_trip_ids)
        valid = picked_off_trip_ids == dropped_off_trip_ids
        self._logger(2, 'Passed' if valid else 'Failed')
        return valid


if __name__ == '__main__':
    from input import stop_times, vehicle_2_stops_times, trips

    tour_generator = TourGenerator(stop_times, vehicle_2_stops_times, trips, 0)

    for vehicle_id in vehicle_2_stops_times.keys():
        print('Vehicle', vehicle_id)
        for i, tour in enumerate(tour_generator.tours(vehicle_id), start=1):
            print('>>> T({},{})'.format(tour.vehicle_id, i), tour)
            print()
