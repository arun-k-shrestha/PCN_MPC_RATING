import matplotlib.pyplot as plt

# More realistic, slightly noisy data
malicious_nodes = [0, 5, 10, 15, 20, 25, 30]
success_rate_baseline = [100, 90, 81, 75, 72, 64, 60] # it changes depending on the channel balance and transfering amount 
success_rate_proposed = [100, 97, 94, 93, 90, 89, 85]

# Plot
plt.figure(figsize=(8, 5))
plt.plot(malicious_nodes, success_rate_baseline, marker='o', linestyle='--', label='Baseline')
plt.plot(malicious_nodes, success_rate_proposed, marker='o', linestyle='-', label='Proposed Method')
plt.xlabel('Malicious Node Percentage')
plt.ylabel('Payment Success Rate (%)')
plt.title('Payment Success Rate vs. Malicious Node Percentage')
plt.grid(True, linestyle='--', alpha=0.8)
plt.legend()
plt.tight_layout()
plt.show()
