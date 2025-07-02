import networkx as nx
import random
import Yao_MPC
import hashlib
import time

# Payment Channel Network (PCN) simulation with MPC (Multi-Party Computation)

# Parameters
NUM_NODES = 1000
NUM_CHANNELS = 4000
MALICIOUS_PERCENTAGES = 0.2 # should be in range from 0-1, [0, 0.1, 0.2, 0.3] -> 0.3 is 30% malicious nodes
MAX_CHANNEL_BALANCE = 1000
MAX_SEND_AMOUNT = 40
MIN_RATING_THRESHOLD = 0 # MIN_RATING_THRESHOLD and MAX_RATING_THRESHOLD are neighborhood rating range the node is comfortable sharing/updating ratings with
MAX_RATING_THRESHOLD = 1
NODE_RATING_UPDATE_PERCENTAGE = 0.9 # goes from 0-1 # 0.9 means 90% of the time the node will update its ratings
MAX_HTLC_ATTEMPTS = 30
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
            balance_uv = random.randint(0, MAX_CHANNEL_BALANCE)
            balance_vu = random.randint(0, MAX_CHANNEL_BALANCE)
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

def find_valid_path_with_mpc_rating(G, sender, receiver, send_amount,  max_attempts=MAX_HTLC_ATTEMPTS ):
    valid_path = None
    visited_edges = set()
    attempts = 0

    while max_attempts > attempts:
        attempts += 1
        path = find_path_dijkstra(G, sender, receiver, exclude_edges=visited_edges)
        if path is None:
            break  # No valid path left

        path_is_valid = True
        for i in range(1,len(path) - 1):
            # Check rating from sender
            current_node = path[i]
            sender_ratings = G.nodes[sender]["rating"]
            if current_node in sender_ratings and (sender_ratings[current_node] <=0):
                path_is_valid = False
                break
            u, v = path[i], path[i + 1]
            balance = get_MAX_channel_balance(G, u, v)
            if G.nodes[v]['honest']: # Assuming all nodes are honest. We are intentionally not checking for malicious nodes here
                if not Yao_MPC.Yao_Millionaires_Protocol(send_amount, balance, 1000, 40): # 40 is the random number
                    #print(f" MPC failed between {u} and {v} (balance: {balance})")
                    visited_edges.add((u, v))
                    path_is_valid = False
                    break

        if path_is_valid:
            valid_path = path
            # print(f"Valid path found: {valid_path}")
            break

    return valid_path


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
    if random.random() < NODE_RATING_UPDATE_PERCENTAGE:
        update_ratings(G)
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

    for i in range(1, len(path)):
        receiver = path[-i]
        sender = path[-i - 1]

        if not knows_preimage[receiver] or not G.nodes[receiver]['honest']:
            # Simulate malicious node refusing to cooperate
            #print(f"Malicious node {receiver} refuses to reveal preimage to {sender}. Payment failed.")
                # Refund all previously locked balances
            for u, v in locked_edges:
                G[u][v]['balance'] += amount # this amount might be negative, becuase the some nodes might have lied during the MPC check   
            if receiver not in G.nodes[mainSender]['rating']:
                G.nodes[mainSender]['rating'][receiver] = -1  # First success
            else:
                G.nodes[mainSender]['rating'][receiver] -= 1  
            return False

        knows_preimage[sender] = True
        G[receiver][sender]['balance'] += amount
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

start = time.time()
for i in range(1000):
    node1 = random.randint(0, NUM_NODES - 1)
    node2 = random.randint(0, NUM_NODES - 1)
    while node1 == node2:
        node2 = random.randint(0, NUM_NODES - 1)
    
    amount = random.randint(1, MAX_SEND_AMOUNT)
    mpc_valid_path= find_valid_path_with_mpc_rating(G, node1, node2, amount)
    # print(mpc_valid_path)
    if mpc_valid_path is not None:
        if simulate_htlc_payment(G, mpc_valid_path, generate_preimage(), amount):
            Sucessful_HTLC += 1
        else:
            Failed_HTLC += 1
end = time.time()
#create_pcn()
print("Successful HTLCs:", Sucessful_HTLC)
print("Failed HTLCs:", Failed_HTLC)
print("Time taken:", end - start, "seconds")
print("End of simulation")

