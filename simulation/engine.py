

from math import inf


class Ambulance:
    def __init__(self, ambulance_id, station_id):
        self.id = ambulance_id
        self.station_id = station_id
        self.state = "Available"
        self.current_location = station_id


class Incident:
    def __init__(self, incident_id, location, arrival_time):
        self.id = incident_id
        self.location = location
        self.arrival_time = arrival_time
        self.status = "Pending"
        self.assigned_ambulance = None
        self.response_time = None


class RoadNetwork:
    def __init__(
        self, stations, areas, cost_matrix,
        closed_roads=None
    ):
        self.stations = stations
        self.areas = areas
        self.roads = {}
        self.closed_roads = set(closed_roads or [])

        for i, station in enumerate(stations):
            for j, area in enumerate(areas):
                self.roads[(station, area)] = cost_matrix[i][j]

    def get_cost(self, station, area):
        i = self.stations.index(station)
        j = self.areas.index(area)

        if (i, j) in self.closed_roads:
            return inf

        return self.roads.get((station, area), inf)


class DispatcherAgent:
    def __init__(
        self, ambulances, allocation_matrix,
        stations, areas, road_network
    ):
        self.ambulances = ambulances
        self.allocation_plan = allocation_matrix
        self.stations = stations
        self.areas = areas
        self.road_network = road_network

        self.remaining_quota = {
            (station, area): int(allocation_matrix[i][j])
            for i, station in enumerate(stations)
            for j, area in enumerate(areas)
        }

        self.response_times = []
        self.failed_incidents = 0

    def dispatch_ambulance(self, incident):
        area = incident.location

        if area not in self.areas:
            incident.status = "Invalid Location"
            self.failed_incidents += 1
            print(f"[FAILED] Unknown area: {area}")
            return None

        # Find available ambulances on routes with
        # a positive allocation quota and valid travel cost.
        candidates = []

        for ambulance in self.ambulances:
            if ambulance.state != "Available":
                continue

            station = ambulance.station_id
            quota = self.remaining_quota.get((station, area), 0)
            cost = self.road_network.get_cost(station, area)

            if quota > 0 and cost < inf:
                candidates.append((cost, station, ambulance))

        # If no allocated route is available, use the
        # fastest available ambulance on any open route.
        if not candidates:
            for ambulance in self.ambulances:
                if ambulance.state != "Available":
                    continue

                station = ambulance.station_id
                cost = self.road_network.get_cost(station, area)

                if cost < inf:
                    candidates.append((cost, station, ambulance))

        if not candidates:
            incident.status = "Unassigned"
            self.failed_incidents += 1
            print(
                f"[FAILED] No available ambulance for "
                f"incident #{incident.id}"
            )
            return None

        cost, station, ambulance = min(
            candidates, key=lambda item: item[0]
        )

        ambulance.state = "Dispatched"
        ambulance.current_location = area

        incident.status = "Assigned"
        incident.assigned_ambulance = ambulance.id
        incident.response_time = cost

        key = (station, area)
        if self.remaining_quota.get(key, 0) > 0:
            self.remaining_quota[key] -= 1

        self.response_times.append(cost)

        print(
            f"[SUCCESS] Incident #{incident.id}: "
            f"Ambulance {ambulance.id}, Station {station}, "
            f"Response time {cost} minutes"
        )

        return ambulance

    def print_performance_summary(self):
        print("\n========== SIMULATION SUMMARY ==========")
        print(f"Assigned incidents: {len(self.response_times)}")
        print(f"Unassigned incidents: {self.failed_incidents}")

        if self.response_times:
            print(
                f"Average response time: "
                f"{sum(self.response_times) / len(self.response_times):.2f}"
            )
            print(f"Maximum response time: {max(self.response_times)}")
            print(f"Minimum response time: {min(self.response_times)}")
        else:
            print("No incidents were assigned.")

        print("========================================")


def run_simulation(
    stations, areas, cost_matrix, allocation_matrix,
    supply, incidents, closed_roads=None
):
    ambulances = [
        Ambulance(f"{station}_Amb{i}", station)
        for index, station in enumerate(stations)
        for i in range(1, supply[index] + 1)
    ]

    network = RoadNetwork(
        stations, areas, cost_matrix, closed_roads
    )

    dispatcher = DispatcherAgent(
        ambulances, allocation_matrix,
        stations, areas, network
    )

    for incident in sorted(
        incidents, key=lambda item: item.arrival_time
    ):
        dispatcher.dispatch_ambulance(incident)

    dispatcher.print_performance_summary()
    return dispatcher
