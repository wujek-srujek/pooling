#!/usr/bin/env python3

from combine import TourCombinator
from log import Logger


class Solver:

    def __init__(self, stop_times, vehicle_2_stops_times, trips, logger_verbosity):
        self._logger = Logger(logger_verbosity)
        self._stop_times = stop_times
        self._vehicle_2_stops_times = vehicle_2_stops_times
        self._trips = trips

    def solve(self):
        shortest_total_time = None
        best_combination = None

        for i, combination in enumerate(TourCombinator(stop_times, vehicle_2_stops_times, trips, 0).combinations(), start=1):
            self._logger(2, 'Considering combination:')
            self._logger.indent()
            for tour in combination:
                self._logger(2, tour)
            self._logger.unindent()
            total_time = sum(map(lambda c: c.total_time, combination))
            self._logger(3, 'Total time:', total_time)
            if shortest_total_time == None or total_time < shortest_total_time:
                self._logger(2, 'Best solution so far')
                shortest_total_time = total_time
                best_combination = combination
            else:
                self._logger(2, 'Better solution already seen:', shortest_total_time)
        return (shortest_total_time, best_combination)


if __name__ == '__main__':
    from input import stop_times, vehicle_2_stops_times, trips

    time, combination = Solver(stop_times, vehicle_2_stops_times, trips, 0).solve()
    print('>>> Total time:', time)
    print('>>> Combination:')
    if combination:
        for tour in combination:
            print(tour)
    else:
        print(combination)
