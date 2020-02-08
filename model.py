from dataclasses import dataclass
from typing import Dict, Set, Tuple
from enum import Enum


@dataclass
class Trip:
    id: str
    pickup_stop_id: str
    dropoff_stop_id: str

class StopType(Enum):
    PICKUP = 0
    DROPOFF = 1

@dataclass
class Stop:
    id: str
    trip_id: str
    type: StopType

@dataclass
class Node:
    stop: Stop
    accumulated_time: int

@dataclass
class Tour:
    vehicle_id: str
    path: str
    nodes: Tuple[Node, ...]
    picked_up_trip_ids_2_nodes: Dict[str, Node]
    dropped_off_trip_ids: Set[str]
    total_time: int
