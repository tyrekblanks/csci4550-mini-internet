import heapq

def build_graph(topology, failed_links=None):
    graph = {}

    if failed_links is None:
        failed_links = []

    for link in topology["links"]:
        node1 = link["node1"]
        node2 = link["node2"]
        cost = link["cost"]

        if node1 not in graph:
            graph[node1] = []

        if node2 not in graph:
            graph[node2] = []
    
        link_is_failed = any(
            (
                failure.get("from") == node1
                and failure.get("to") == node2
            )
            or (
                failure.get("from") == node2
                and failure.get("to") == node1
            )
            for failure in failed_links
        )

        if link_is_failed:
            continue

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

            elif new_distance == distances[neighbor]:
                current_previous = previous.get(neighbor)

                if current_previous is None or current_router < current_previous:
                    previous[neighbor] = current_router

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