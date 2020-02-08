#!/usr/bin/env python3

from tour import TourGenerator
from log import Logger
from itertools import product


class TourCombinator:

    def __init__(self, stop_times, vehicle_2_stops_times, trips, logger_verbosity):
        self._logger = Logger(logger_verbosity)
        self._stop_times = stop_times
        self._vehicle_2_stops_times = vehicle_2_stops_times
        self._vehicles = list(vehicle_2_stops_times.keys())
        self._trips = trips
        self._all_trip_ids = list(map(lambda t: t.id, self._trips))

    def combinations(self):
        vehicle_2_tours = lambda v: TourGenerator(self._stop_times, self._vehicle_2_stops_times, self._trips, 0).tours(v)
        tour_generators = map(vehicle_2_tours, self._vehicles)
        for candidate_combination in product(*tour_generators):
            self._logger(1, 'Candidate combination:')
            self._logger.indent()
            for tour in candidate_combination:
                self._logger(1, tour)
            self._logger.unindent()

            if not self._trips_handled_by_one_tour(candidate_combination):
                self._logger(1, 'Rejected (duplicate trips)')
                continue

            if not self._is_complete(candidate_combination):
                self._logger(1, 'Rejected (not all trips are served)')
                continue

            self._logger(1, 'Accepted')
            yield candidate_combination

    def _trips_handled_by_one_tour(self, combination):
        # condition 4
        self._logger(2, 'Are trips handled by one tour?')
        # iterate over trip ids of each tour and check if any has been seen yet
        # break early if found
        valid = True
        seen_trip_ids = set()
        for tour in combination:
            if not valid: break
            for trip_id in tour.dropped_off_trip_ids:
                if trip_id in seen_trip_ids:
                    valid = False
                    break
                seen_trip_ids.add(trip_id)
        self._logger(2, 'Passed' if valid else 'Failed')
        return valid

    def _is_complete(self, combination):
        self._logger(2, 'Are all trips served?')
        combined_trip_ids = set.union(*map(lambda t: set(t.picked_up_trip_ids_2_nodes.keys()), combination))
        self._logger(3, 'Combined trip ids:', combined_trip_ids, 'all trip ids:', self._all_trip_ids)
        valid = len(combined_trip_ids) == len(self._trips)
        self._logger(2, 'Passed' if valid else 'Failed')
        return valid


if __name__ == '__main__':
    from input import stop_times, vehicle_2_stops_times, trips

    combinator = TourCombinator(stop_times, vehicle_2_stops_times, trips, 0)

    for i, combination in enumerate(combinator.combinations(), start=1):
        print('>>> C({})'.format(i))
        for tour in combination:
            print(tour)
        print()
