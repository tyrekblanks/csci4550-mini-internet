import heapq

def build_graph(topology):
    graph = {}

    for link in topology["links"]:
        node1 = link["node1"]
        node2 = link["node2"]
        cost = link["cost"]

        if node1 not in graph:
            graph[node1] = []

        if node2 not in graph:
            graph[node2] = []

        graph[node1].append((node2, cost))
        graph[node2].append((node1, cost))

    return graph

def dijkstra(graph, start):
    distances = {}
    previous = {}

    for router in graph:
        distances[router] = float("inf")

    distances[start] = 0
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_router = heapq.heappop(priority_queue)

        if current_distance > distances[current_router]:
            continue

        for neighbor, cost in graph[current_router]:
            new_distance = current_distance + cost

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_router
                heapq.heappush(priority_queue, (new_distance, neighbor))

    return distances, previous

def get_next_hop(previous, start, destination):
    current = destination

    while previous.get(current) != start:
        current = previous.get(current)

        if current is None:
            return None

    return current

def build_routing_table(graph, start):
    distances, previous = dijkstra(graph, start)
    routing_table = {}

    for destination in graph:
        if destination == start:
            continue

        next_hop = get_next_hop(previous, start, destination)

        if next_hop is not None:
            routing_table[destination] = next_hop

    return routing_table

if __name__ == "__main__":
    test_topology = {
        "links": [
            {"node1": "RouterA", "node2": "RouterB", "cost": 1},
            {"node1": "RouterA", "node2": "RouterC", "cost": 1},
            {"node1": "RouterB", "node2": "RouterD", "cost": 1},
            {"node1": "RouterC", "node2": "RouterD", "cost": 1}
        ]
    }

    graph = build_graph(test_topology)
    print(build_routing_table(graph, "RouterA"))