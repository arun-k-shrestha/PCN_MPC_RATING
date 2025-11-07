import networkx as nx
import random
import Yao_MPC
import hashlib
import time

# Payment Channel Network (PCN) simulation with MPC (Multi-Party Computation)

# Parameters
NUM_NODES = 100
NUM_CHANNELS = 400
MALICIOUS_PERCENTAGES = 0 # should be in range from 0-1, [0, 0.1, 0.2, 0.3] -> 0.3 is 30% malicious nodes
MAX_CHANNEL_BALANCE = 1000
MAX_SEND_AMOUNT = 100
MIN_RATING_THRESHOLD = 0 # MIN_RATING_THRESHOLD and MAX_RATING_THRESHOLD are neighborhood rating range the node is comfortable sharing/updating ratings with
MAX_RATING_THRESHOLD = 1
NODE_RATING_UPDATE_PERCENTAGE = 0.9 # goes from 0-1 # 0.9 means 90% of the time the node will update its ratings
MAX_HTLC_ATTEMPTS = 10
Sucessful_HTLC = 0
Failed_HTLC = 0

# Initialize the graph
def create_pcn():
    G = nx.DiGraph()
    for i in range(NUM_NODES):
        G.add_node(i, honest=True, rating={})
    #print(G.nodes(data=True))

    edges = set()
    while len(edges) < NUM_CHANNELS:
        u, v = random.sample(range(NUM_NODES), 2)
        if u != v and (u, v) not in edges and (v, u) not in edges:
            # Each direction has its own balance
            balance_uv = random.randint(1, MAX_CHANNEL_BALANCE)
            balance_vu = random.randint(1, MAX_CHANNEL_BALANCE)
            G.add_edge(u, v, balance=balance_uv)
            G.add_edge(v, u, balance=balance_vu)
            edges.add((u, v))
    #print(G.nodes(data=True))
    #print(G.edges(data=True))
    return G

G = create_pcn()



# Mark some nodes as malicious
def make_malicious(G, percent):
    malicious_nodes = random.sample(list(G.nodes()), int(NUM_NODES * percent))
    for node in malicious_nodes:
        G.nodes[node]["honest"] = False

make_malicious(G,MALICIOUS_PERCENTAGES) #0.5 is 50% malicious nodes


def get_MAX_channel_balance(G, u, v):
    return G[u][v]['balance'] if G.has_edge(u, v) else 0

# Dijkstra that skips excluded edges
def find_path_dijkstra(G, sender, receiver, exclude_edges=set()):
    G_temp = G.copy()
    G_temp.remove_edges_from(exclude_edges)
    try:
        path = nx.dijkstra_path(G_temp, sender, receiver)
        #print(f"Path found: {path}")
        return path
    except nx.NetworkXNoPath:
        #print("No path found.")
        return None
    

def find_path_bfs(G, sender, receiver, exclude_edges=None):
    if exclude_edges is None:
        exclude_edges = set()

    # Fast, no-copy view: keeps all nodes, hides excluded edges
    view = nx.subgraph_view(G, filter_edge=lambda u, v: (u, v) not in exclude_edges)

    try:
        # Unweighted shortest path (bidirectional BFS where applicable)
        return nx.shortest_path(view, sender, receiver)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def find_valid_path_HTLC_Helper(G, sender, receiver, send_amount, max_attempts=10):
    visited_edges = set()
    attempts = 0

    while attempts < max_attempts:
        path = find_path_bfs(G, sender, receiver, visited_edges)
        if path is None:
            return None  # no path left
        path_is_valid = True
        for u, v in zip(path, path[1:]):
            current_node = v
            sender_ratings = G.nodes[sender]["rating"]
            if current_node in sender_ratings and (sender_ratings[current_node] <=0):
                path_is_valid = False
                break
            if G[u][v]['balance'] < send_amount:
                visited_edges.add((u, v))
                # preserve your per-edge failure accounting
                global Failed_HTLC
                Failed_HTLC += 1
                path_is_valid = False
                break

        if path_is_valid:
            return path
        attempts += 1
    return None

def find_valid_path_with_mpc(G, sender, receiver, send_amount, max_attempts=MAX_HTLC_ATTEMPTS):
    visited_edges = set()
    attempts = 0

    while attempts < max_attempts:
        path = find_path_bfs(G, sender, receiver, visited_edges)
        if path is None:
            return None  # no path left
        path_is_valid = True
        # IMPORTANT: don't skip the first edge; use zip

        for u, v in zip(path, path[1:]):
            current_node = u
            sender_ratings = G.nodes[sender]["rating"]
            if current_node in sender_ratings and (sender_ratings[current_node] <=0):
                path_is_valid = False
                break

            # # Cheap short-circuit before MPC (optional; preserves result semantics)
            # bal = G[u][v]['balance']
            # if G.nodes[v]['honest']:
            #     # the third parameter in Yao_Millionaires_Protocol should be set to a value greater than the balance
            #     if not Yao_MPC.Yao_Millionaires_Protocol(send_amount, bal, MAX_SEND_AMOUNT+bal, 40):
            #         visited_edges.add((u, v))
            #         # If your channels are effectively bidirectional, you may also:
            #         # visited_edges.add((v, u))
            #         path_is_valid = False
            #         break
        if path_is_valid:
            return path

        attempts += 1

    return None



def update_ratings(G):
    for node in G.nodes():
        rating_threshold = random.randint(MIN_RATING_THRESHOLD,MAX_RATING_THRESHOLD)
        neighbors = list(G.neighbors(node))
        node_rating = G.nodes[node]['rating']
        if not node_rating:
            continue  # no trust yet, skip

        for neighbor in neighbors:
            # Only trust ratings from neighbors you rate highly
            if neighbor not in node_rating or node_rating[neighbor] < rating_threshold:
                continue
            neighbor_ratings = G.nodes[neighbor]['rating']

            for rated_node, score in neighbor_ratings.items():
                if rated_node == node or rated_node == neighbor:
                    continue  # skip self or mutual rating loops
                if rated_node in node_rating:
                    continue  # already rated → skip
                if score >= rating_threshold:
                    node_rating[rated_node] = 1
                elif score <= -rating_threshold:
                    node_rating[rated_node] = -1


def generate_preimage():
    return str(random.randint(100000, 999999)) 


def hash_preimage(preimage):
    return hashlib.sha256(preimage.encode()).hexdigest()

def simulate_htlc_payment(G, path, preimage, amount):
    # if random.random() < NODE_RATING_UPDATE_PERCENTAGE:
    #     update_ratings(G)
        #print("update",G.nodes(data=True))
    mainSender = path[0]
    H = hash_preimage(preimage)
    # Step 0: Lock funds (forward direction)
    locked_edges = []

    # Step 1: Lock funds (forward direction)
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        #print("initital balance", G[u][v]['balance'])
        G[u][v]['balance'] -= amount
        locked_edges.append((u, v))  # Track for refund if needed in case of HTLC failure

    # Step 2: Preimage revelation (backward) — simulate malicious behavior
    knows_preimage = {node: False for node in path} # Initialize knowledge of preimage and every node starts with not knowing it
    knows_preimage[path[-1]] = True  # Receiver knows it

    reverse_credit = [] # To track balances to be credited in reverse direction
    for i in range(1, len(path)):
        receiver = path[-i]
        sender = path[-i - 1]

        if not knows_preimage[receiver] or not G.nodes[receiver]['honest']:
            # Simulate malicious node refusing to cooperate
            #print(f"Malicious node {receiver} refuses to reveal preimage to {sender}. Payment failed.")
                # Refund all previously locked balances
            for u, v in locked_edges:
                G[u][v]['balance'] += amount # this amount might be negative, becuase the some nodes might have lied during the MPC check  
            for x,y in reverse_credit:
                G[x][y]['balance'] -= amount 
            if receiver not in G.nodes[mainSender]['rating']:
                G.nodes[mainSender]['rating'][receiver] = -1  # First success
            else:
                G.nodes[mainSender]['rating'][receiver] -= 1  
            return False

        knows_preimage[sender] = True
        G[receiver][sender]['balance'] += amount
        reverse_credit.append((receiver, sender))
        # print(f"{sender} receives {amount} from {receiver}. New balance: {G[receiver][sender]['balance']}")
    

    # HTLC successful: update sender’s ratings
    for i in range(1, len(path)):
        node = path[i]
        if node not in G.nodes[mainSender]['rating']:
            G.nodes[mainSender]['rating'][node] = 1  # First success
        else:
            G.nodes[mainSender]['rating'][node] += 1  # Increment existing score

    #print("HTLC payment completed successfully!\n")

    # update entire node ratings with probabilty of NODE_RATING_UPDATE:
    return True

# print(G.nodes(data=True))
# print("")
# print(G.edges(data=True))

success_rate_rating  = []
for i in range(13):
    G = create_pcn()
    make_malicious(G,MALICIOUS_PERCENTAGES)
    # print("Initial node ratings:", G.nodes(data=True))
    # print("Initial edge balances:", G.edges(data=True))
    Sucessful_HTLC = 0
    Failed_HTLC = 0

    start = time.time()
    for i in range(10000):
        # if i % 1000 == 0:
        #     print("Transaction:", i)
        node1 = random.randint(0, NUM_NODES - 1)
        node2 = random.randint(0, NUM_NODES - 1)
        while node1 == node2:
            node2 = random.randint(0, NUM_NODES - 1)
        amount = random.randint(1, MAX_SEND_AMOUNT)

        shortest_path= find_valid_path_HTLC_Helper(G, node1, node2, amount,MAX_HTLC_ATTEMPTS)
        if shortest_path is not None:
            if simulate_htlc_payment(G, shortest_path, generate_preimage(), amount):
                Sucessful_HTLC += 1
            else:
                Failed_HTLC += 1
    end = time.time()

    #create_pcn()
    print("------ Malicious:,", MALICIOUS_PERCENTAGES, "------")
    print("Successful HTLCs:", Sucessful_HTLC)
    print("Failed HTLCs:", Failed_HTLC)
    print("Total HTLCs:", Sucessful_HTLC + Failed_HTLC)
    print("Success Rate:", Sucessful_HTLC / (Sucessful_HTLC + Failed_HTLC) * 100 if (Sucessful_HTLC + Failed_HTLC) > 0 else 0, "%")
    print("Time taken:", end - start, "seconds")
    print("End of simulation")
    print("===================================")
    success_rate_rating.append(round(Sucessful_HTLC / (Sucessful_HTLC + Failed_HTLC) * 100, 1))
    MALICIOUS_PERCENTAGES += 0.025

print("success_rate_rating= ",success_rate_rating)


