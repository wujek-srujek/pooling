#!/usr/bin/env python3

verbosityt = 0

def _1t(*args):
    if verbosityt >= 1: print(*args)

def _2t(*args):
    if verbosityt >= 2: print(*args)

def _3t(*args):
    if verbosityt >= 3: print(*args)

#####################################

costs = {
    'P1': {'P1': 0,  'D1': 10, 'P2': 2,  'D2': 9,  'P3': 2,  'D3': 9},
    'D1': {'P1': 10, 'D1': 0,  'P2': 8,  'D2': 12, 'P3': 2,  'D3': 9},
    'P2': {'P1': 2,  'D1': 8,  'P2': 0,  'D2': 6,  'P3': 2,  'D3': 9},
    'D2': {'P1': 9,  'D1': 12, 'P2': 6,  'D2': 0,  'P3': 2,  'D3': 9},
    # 'P3': {'P1': 2,  'D1': 8,  'P2': 0,  'D2': 6,  'P3': 2,  'D3': 9},
    # 'D3': {'P1': 9,  'D1': 12, 'P2': 6,  'D2': 0,  'P3': 2,  'D3': 9},
    'V1': {'P1': 1,  'D1': 11, 'P2': 3,  'D2': 7,  'P3': 2,  'D3': 9},
    'V2': {'P1': 7, 'D1': 10,  'P2': 2,  'D2': 3,  'P3': 2,  'D3': 9},
}

stops = list(filter(lambda k: not k.startswith('V'), costs.keys()))
requests_count = len(stops)//2

pickup_time_limit = 15

travel_time_ratio_limit = 1.5 # 50% longer than direct trip

#####################################

def pickup_within_time_limit(acc_cost):
    # condition 1
    return acc_cost <= pickup_time_limit

def each_pickup_is_before_dropoff(nodes):
    pickups = set()
    for node in nodes:
        stop = node['stop']
        if stop[0] == 'P':
            pickups.add(stop[1])
        else:
            # must be dropp off
            if stop[1] not in pickups:
                return False
    return True

def each_pickup_has_dropoff(nodes, indent):
    # condition 5
    pickups = set(map(lambda n: n['stop'][1:], filter(lambda n: n['stop'][0] == 'P', nodes)))
    dropoffs = set(map(lambda n: n['stop'][1:], filter(lambda n: n['stop'][0] == 'D', nodes)))
    _3t('{}(?3) pickups:'.format(indent), pickups)
    _3t('{}(?3) dropoffs:'.format(indent), dropoffs)
    return pickups == dropoffs

def travel_time_within_time_limit(nodes, indent):
    # condition 2
    # this function is always called for a dropoff at the end
    dropoff_node = nodes[-1]
    dropoff_stop = dropoff_node['stop']
    _3t('{}(?4) nodes:'.format(indent), nodes)
    _3t('{}(?4) dropoff node:'.format(indent), dropoff_node)
    assert dropoff_stop[0] == 'D'
    # a pickup for the drop off
    pickup_node = next(n for n in nodes if n['stop'] == 'P{}'.format(dropoff_stop[1]))
    _3t('{}(?4) found pickup node:'.format(indent), pickup_node)
    travel_time = dropoff_node['acc_cost'] - pickup_node['acc_cost']
    _3t('{}(?4) travel time:'.format(indent), travel_time)
    direct_connection = costs[pickup_node['stop']][dropoff_stop]
    _3t('{}(?4) direct connection:'.format(indent), direct_connection)
    return travel_time <= travel_time_ratio_limit * direct_connection

def accumulated_cost(v, nodes, stop, indent):
    if len(nodes):
        fro = nodes[-1]
        _3t('{}($$) using [{}] as from'.format(indent, fro))
        from_stop = fro['stop']
        new_cost = costs[from_stop][stop]
        _3t('{}($$) new cost({}, {})=[{}]'.format(indent, from_stop, stop, new_cost))
        accumulated_cost = fro['acc_cost'] + new_cost
    else:
        _3t('{}($$) nothing accumulated, using vehicle [{}] as from'.format(indent, v))
        new_cost = costs[v][stop]
        _3t('{}($$) new cost({}, {})=[{}]'.format(indent, v, stop, new_cost))
        accumulated_cost = new_cost
    _3t('{}($$) accumulated cost = [{}]'.format(indent, accumulated_cost))
    return accumulated_cost

def branches(v, stops, accumulator={'path': '', 'bookings': set(), 'nodes': (), 'cost': 0}):
    nodes = accumulator['nodes']
    if not nodes:
        # initial, empty branch, means the car doesn't have to do anything as
        # other cars take over, which is a valid option
        yield accumulator
        _2t()
    # each iteration uses one element + recursively the list minus the current element
    indent = '.' * (len(nodes)+1)
    for i, stop in enumerate(stops):
        _3t('{}($$) calculating accumulated cost: vehicle: [{}], accumulator [{}], stop [{}]'.format(indent, v, accumulator, stop))
        acc_cost = accumulated_cost(v, nodes, stop, indent)
        node = {'stop': stop, 'acc_cost': acc_cost}
        candidate_nodes = nodes + (node,)
        candidate = {
            'path': accumulator['path']+stop,
            'bookings': accumulator['bookings'] | {stop[1]},
            'nodes': candidate_nodes,
            'cost': acc_cost
        }
        _2t('{} stop [{}], candidate [{}]'.format(indent, stop, candidate))
        if stop[0] == 'P':
            _3t('{}(?1) pickup within time limit'.format(indent))
            if not pickup_within_time_limit(acc_cost):
                _2t('{}(?1)- rejected'.format(indent))
                _2t('{} --- cutting short, branch can never be valid'.format(indent))
                # cut short, no need to go deeper, this branch is invalid
                _2t()
                continue
        _3t('{}(?1) passed'.format(indent))
        _3t('{}(?2) each pickup is before dropoff'.format(indent))
        if not each_pickup_is_before_dropoff(candidate_nodes):
            _2t('{}(?2)- rejected'.format(indent))
            _2t('{} --- cutting short, branch can never be valid'.format(indent))
            # cut short, no need to go deeper, this branch is invalid
            _2t()
            continue
        _3t('{}(?2) passed'.format(indent))
        _3t('{}(?3) each pickup has dropoff'.format(indent))
        if not each_pickup_has_dropoff(candidate_nodes, indent):
            _2t('{}(?3) - rejected'.format(indent))
            # rejected, but maybe deeper branches are good, do not cut short
        else:
            _3t('{}(?3) passed'.format(indent))
            if stop[0] == 'D':
                _3t('{}(?4) travel time within time limit'.format(indent))
                if not travel_time_within_time_limit(candidate_nodes, indent):
                    _2t('{}(?4)- rejected'.format(indent))
                    _2t('{} --- cutting short, branch can never be valid'.format(indent))
                    # cut short, no need to go deeper, this branch is invalid
                    _2t()
                    continue
            _2t('{} + accepted'.format(indent))
            yield candidate
        _2t()
        sublist = stops[:i] + stops[i+1:]
        if not sublist:
            # list exhausted
            continue
        yield from branches(v, sublist, candidate)

def tagged_branches(v, points):
    for i, branch in enumerate(branches(v, stops), start=1):
        yield { 'id': 'T({},{})'.format(v, i), **branch }

def print_branches(branches):
    for branch in branches:
        _1t(branch)
    _1t()

print_branches(tagged_branches('V1', stops))
print_branches(tagged_branches('V2', stops))

#####################################

verbosityc = 0

def _1c(*args):
    if verbosityc >= 1: print(*args)

def _2c(*args):
    if verbosityc >= 2: print(*args)

def _3c(*args):
    if verbosityc >= 3: print(*args)

#####################################

def combinations():
    for bv1 in tagged_branches('V1', stops):
        for bv2 in tagged_branches('V2', stops):
            if bv1['path'] != bv2['path']:
                yield (bv1, bv2)
                _2c()

def has_duplicate_bookings(combo):
    # condition 4
    v1_bookings = combo[0]['bookings']
    _3c('(?1) v1_bookings:', v1_bookings)
    v2_bookings = combo[1]['bookings']
    _3c('(?1) v2_bookings:', v2_bookings)
    common = v1_bookings & v2_bookings
    _3c('(?1) common elements:', common)
    return bool(common)

def is_complete(combo):
    v1_bookings = combo[0]['bookings']
    _3c('(?2) v1_bookings:', v1_bookings)
    v2_bookings = combo[1]['bookings']
    _3c('(?2) v2_bookings:', v2_bookings)
    union = v1_bookings | v2_bookings
    _3c('(?2) combined bookings:', union)
    return len(union) == requests_count

def valid_combinations():
    for combo in combinations():
        _2c('processing', combo)
        _3c('(?1) has duplicate bookings')
        if has_duplicate_bookings(combo):
            _2c('(?1)- rejected')
            continue
        _3c('(?1) passed')
        _3c('(?2) is complete')
        if not is_complete(combo):
            _2c('(?2)- rejected')
            continue
        _2c('+ accepted')
        yield combo

for i, combo in enumerate(valid_combinations(), start=1):
    _1c(i, combo)

#####################################

verbositys = 2

def _1s(*args):
    if verbositys >= 1: print(*args)

def _2s(*args):
    if verbositys >= 2: print(*args)

def _3s(*args):
    if verbositys >= 3: print(*args)

#####################################

best = None
lowest_cost = None

for i, combo in enumerate(valid_combinations(), start=1):
    _2s(i, ':', combo)
    cost = combo[0]['cost'] + combo[1]['cost']
    _2s('($$) cost:', cost)
    if lowest_cost == None or cost < lowest_cost:
        _2s('($$) best solution so far')
        _2s()
        best = combo
        lowest_cost = cost

_2s()
print('solution:', best)
