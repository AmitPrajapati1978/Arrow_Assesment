import time
import json
import matplotlib.pyplot as plt

from Objective_A import run_object_a
from Objective_B import run_object_b
from Objective_C import run_object_c
from Objective_D import run_object_d


SAMPLE_FILES = {
    1_000: "Sample_data/inventory_1000.json",
    10_000: "Sample_data/inventory_10000.json",
    20_000: "Sample_data/inventory_20000.json",
    50_000: "Sample_data/inventory_50000.json",
    100_000: "Sample_data/inventory_100000.json",
}

import os

def clear_mapping_cache():
    mapping_dir = "mapping_folder"
    if not os.path.exists(mapping_dir):
        return

    for file in os.listdir(mapping_dir):
        if file.endswith(".json"):
            os.remove(os.path.join(mapping_dir, file))


results = []

for size, path in SAMPLE_FILES.items():
    print(f"\nProcessing {size} records...")
    clear_mapping_cache()

    start = time.perf_counter()

    data_a = run_object_a(path)
    data_b = run_object_b(data_a)
    data_c = run_object_c(data_b)
    run_object_d(data_c, output_path=f"Sample_data/benchmark_output_{size}.json")

    end = time.perf_counter()

    elapsed = end - start
    results.append((size, elapsed))

    print(f"Time taken: {elapsed:.2f} seconds")


# ---------------------
# Plot results
# ---------------------
sizes = [r[0] for r in results]
times = [r[1] for r in results]

plt.figure(figsize=(8, 5))
plt.plot(sizes, times, marker="o")
plt.xlabel("Number of Records")
plt.ylabel("Processing Time (seconds)")
plt.title("Pipeline Performance Benchmark")
plt.grid(True)

plt.savefig("benchmark_performance.png")
plt.show()
