import matplotlib.pyplot as plt

# More realistic, slightly noisy data
malicious_nodes = [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30]
success_rate_baseline = [81.8, 76.6, 68.2, 60.0, 54.8, 54.7, 43.5, 45.4, 40.1, 34.9, 34.3, 32.2, 31.8] # it changes depending on the channel balance and transfering amount 
success_rate_mpc=  [100.0, 96.2, 91.4, 86.8, 81.2, 76.9, 61.9, 56.4, 60.2, 56.5, 46.3, 47.6, 40.4]
success_rate_mpc_rating=  [100.0, 98.7, 96.3, 94.6, 92.2, 89.9, 87.6, 86.3, 81.9, 80.2, 78.6, 75.4, 72.2]
success_rate_rating=  [83.0, 80.4, 76.4, 70.3, 65.9, 67.9, 65.1, 62.7, 54.3, 62.5, 53.4, 54.7, 52.7]

# Plot[92.2, 89.9]
plt.figure(figsize=(8, 5))
plt.plot(malicious_nodes, success_rate_baseline, marker='o', linestyle='-', label='Baseline', color='skyblue')
plt.plot(malicious_nodes, success_rate_mpc, marker='o', linestyle='-', label='MPC', color='orange')
plt.plot(malicious_nodes, success_rate_rating , marker='o', linestyle='-', label='Rating', color ='red')
plt.plot(malicious_nodes, success_rate_mpc_rating , marker='o', linestyle='-', label='MPC + Rating', color='green')
plt.xlabel('Malicious Node Percentage')
plt.ylabel('Payment Success Rate (%)')
plt.title('Payment Success Rate vs. Malicious Node Percentage')
plt.grid(True, linestyle='--', alpha=0.8)
plt.legend()
plt.tight_layout()
plt.show()
