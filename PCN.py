import networkx as nx
import random
import hashlib
import time

# Payment Channel Network (PCN) simulation WITHOUT MPC (Multi-Party Computation)


# Parameters
NUM_NODES = 1000
NUM_CHANNELS = 4000
MALICIOUS_PERCENTAGES = 0.2 #[0, 0.1, 0.2, 0.3] #0.3 is 30% malicious nodes
TRANSACTIONS_AMOUNT = 1000
SEND_AMOUNT = 40
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
            balance_uv = random.randint(0, TRANSACTIONS_AMOUNT)
            balance_vu = random.randint(0, TRANSACTIONS_AMOUNT)
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

make_malicious(G,MALICIOUS_PERCENTAGES)


def get_channel_balance(G, u, v):
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
    

def find_valid_path_WITHOUT_mpc(G, sender, receiver, send_amount):
    valid_path = None
    visited_edges = set()

    while True:
        path = find_path_dijkstra(G, sender, receiver, exclude_edges=visited_edges)
        if path is None:
            break  # No valid path left

        path_is_valid = True
        for i in range(1,len(path) - 1):
            u, v = path[i], path[i + 1]
            balance = get_channel_balance(G, u, v)
            if balance < send_amount: 
                visited_edges.add((u, v))
                path_is_valid = False
                global Failed_HTLC # updating the global variable
                Failed_HTLC += 1
                break

        if path_is_valid:
            valid_path = path
            #print(f"Valid path found: {valid_path}")
            break

    return valid_path


def generate_preimage():
    return str(random.randint(100000, 999999)) 


def hash_preimage(preimage):
    return hashlib.sha256(preimage.encode()).hexdigest()

def simulate_htlc_payment(G, path, preimage, amount):
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

        if knows_preimage[receiver]:
            # Simulate malicious node refusing to cooperate
            if not G.nodes[receiver]['honest']:
                #print(f"Malicious node {receiver} refuses to reveal preimage to {sender}. Payment failed.")
                 # Refund all previously locked balances
                for u, v in locked_edges:
                    G[u][v]['balance'] += amount # this amount might be negative, becuase the nodes might have lied during the balance checking  
                return False

            knows_preimage[sender] = True
            G[receiver][sender]['balance'] += amount
            #print(f"{sender} receives {amount} from {receiver}. New balance: {G[receiver][sender]['balance']}")
        else:
            for u, v in locked_edges:
                G[u][v]['balance'] += amount 
            return False

    #print("HTLC payment completed successfully!\n")
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
    amount = random.randint(1, SEND_AMOUNT)

    shortest_path= find_valid_path_WITHOUT_mpc(G, node1, node2, amount)
    if shortest_path is not None:
        if simulate_htlc_payment(G, shortest_path, generate_preimage(), amount):
            Sucessful_HTLC += 1
        else:
            Failed_HTLC += 1
end = time.time()

#create_pcn()
print("Successful HTLCs:", Sucessful_HTLC)
print("Failed HTLCs:", Failed_HTLC)
print("Time taken:", end - start, "seconds")
print("End of simulation")