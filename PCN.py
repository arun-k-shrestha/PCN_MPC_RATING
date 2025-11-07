import networkx as nx
import random
import hashlib
import time

# Payment Channel Network (PCN) simulation WITHOUT MPC (Multi-Party Computation)


# Parameters
NUM_NODES = 100
NUM_CHANNELS = 400
MAX_CHANNEL_BALANCE= 1000
MAX_SEND_AMOUNT = 100
MALICIOUS_PERCENTAGES = 0 #[0, 0.1, 0.2, 0.3] #0.3 is 30% malicious nodes
MAX_ATTEMPTS = 10 # Max attempts to find a valid path
Sucessful_HTLC = 0
Failed_HTLC = 0

# Initialize the graph
def create_pcn():
    G = nx.DiGraph()
    for i in range(NUM_NODES):
        G.add_node(i, honest=True)
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
    # print(G.nodes(data=True))
    # print(G.edges(data=True))
    return G


# Mark some nodes as malicious
def make_malicious(G, percent):
    malicious_nodes = random.sample(list(G.nodes()), int(NUM_NODES * percent))
    for node in malicious_nodes:
        G.nodes[node]["honest"] = False


def get_channel_balance(G, u, v):
    return G[u][v]['balance'] if G.has_edge(u, v) else 0
    

def find_path_bfs(G, sender, receiver, exclude_edges=None):
    if exclude_edges is None:
        exclude_edges = set()
    view = nx.subgraph_view(G, filter_edge=lambda u, v: (u, v) not in exclude_edges)

    try:
        return nx.shortest_path(view, sender, receiver)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def find_valid_path_HTLC_Helper(G, sender, receiver, send_amount, max_attempts=10):
    visited_edges = set()
    attempts = 0
    local_failures = 0
    while attempts < max_attempts:
        path = find_path_bfs(G, sender, receiver, visited_edges)
        if path is None:
            return None, local_failures  # no path left
        path_is_valid = True
        for u, v in zip(path, path[1:]):
            if G[u][v]['balance'] < send_amount:
                visited_edges.add((u, v))
                # preserve your per-edge failure accounting
                local_failures += 1
                path_is_valid = False
                break

        if path_is_valid:
            return path, local_failures 
        attempts += 1
    return None, local_failures



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

    reverse_credit = [] # To track balances to be credited in reverse direction
    for i in range(1, len(path)):
        receiver = path[-i]
        sender = path[-i - 1]

        if knows_preimage[receiver]:
            # Simulate malicious node refusing to cooperate
            if not G.nodes[receiver]['honest']:
                #print(f"Malicious node {receiver} refuses to reveal preimage to {sender}. Payment failed.")
                 # Refund all previously locked balances
                for x,y in reverse_credit:
                    G[x][y]['balance'] -= amount
                for u, v in locked_edges:
                    G[u][v]['balance'] += amount # this amount might be negative, becuase the nodes might have lied during the balance checking
                return False

            knows_preimage[sender] = True
            G[receiver][sender]['balance'] += amount
            reverse_credit.append((receiver, sender))
            #print(f"{sender} receives {amount} from {receiver}. New balance: {G[receiver][sender]['balance']}")
        else:
             # Refund all previously locked balances
            for x,y in reverse_credit:
                G[x][y]['balance'] -= amount
            for u, v in locked_edges:
                G[u][v]['balance'] += amount 
            return False

    #print("HTLC payment completed successfully!\n")
    return True
# print(G.nodes(data=True))
# print("")
# print(G.edges(data=True))
success_rate_baseline  = []
for i in range(13):

    G = create_pcn()
    make_malicious(G,MALICIOUS_PERCENTAGES)
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

        shortest_path, local_failures = find_valid_path_HTLC_Helper(G, node1, node2, amount,MAX_ATTEMPTS)
        Failed_HTLC += local_failures
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
    success_rate_baseline.append(round(Sucessful_HTLC / (Sucessful_HTLC + Failed_HTLC) * 100, 1))

    MALICIOUS_PERCENTAGES+=0.025
print("success_rate_baseline= ",success_rate_baseline)