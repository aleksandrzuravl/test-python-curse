#!/usr/bin/env python3
"""
Stress test script for ThreadSafeHashTable
Performs 5,000,000+ operations with 75%+ read operations
"""

import time
import threading
import random
from project.hashtable.threaded_hash_table import ThreadSafeHashTable, NonThreadSafeHashTable


def run_mega_stress_test():
    """Run stress test with 5,000,000+ operations"""
    print("=== MEGA STRESS TEST ===")
    print("Target: 5,000,000+ operations with 75%+ reads")
    print()

    # Configuration
    total_operations = 5_000_000
    read_ratio = 0.75  # 75% reads
    num_threads = 8
    operations_per_thread = total_operations // num_threads

    # Initialize hash table
    hash_table = ThreadSafeHashTable(initial_capacity=1024)

    # Pre-populate with initial data
    print("Pre-populating with initial data...")
    for i in range(10000):
        hash_table[f"init_key_{i}"] = f"init_value_{i}"

    # Statistics
    operations_completed = [0]
    reads_completed = [0]
    writes_completed = [0]
    deletes_completed = [0]
    errors = []

    def stress_worker(worker_id):
        """Worker function for stress testing"""
        local_reads = 0
        local_writes = 0
        local_deletes = 0

        try:
            for i in range(operations_per_thread):
                op_type = random.random()

                if op_type < read_ratio:  # Read operation (75%)
                    key = f"init_key_{random.randint(0, 9999)}"
                    _ = hash_table.get(key, "default")
                    local_reads += 1

                elif op_type < 0.90:  # Write operation (15%)
                    key = f"worker_{worker_id}_key_{i}"
                    hash_table[key] = f"worker_{worker_id}_value_{i}"
                    local_writes += 1

                else:  # Delete operation (10%)
                    key = f"init_key_{random.randint(0, 999)}"
                    if key in hash_table:
                        del hash_table[key]
                    local_deletes += 1

                operations_completed[0] += 1

                # Progress reporting
                if operations_completed[0] % 500000 == 0:
                    print(f"Progress: {operations_completed[0]:,} operations completed")

            # Update global statistics
            with threading.Lock():
                reads_completed[0] += local_reads
                writes_completed[0] += local_writes
                deletes_completed[0] += local_deletes

        except Exception as e:
            errors.append(e)
            print(f"Error in worker {worker_id}: {e}")

    # Create and start threads
    print(f"Starting {num_threads} worker threads...")
    threads = []
    start_time = time.time()

    for i in range(num_threads):
        thread = threading.Thread(target=stress_worker, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    end_time = time.time()
    total_time = end_time - start_time

    # Print results
    print("\n=== STRESS TEST RESULTS ===")
    print(f"Total operations: {operations_completed[0]:,}")
    print(f"Read operations:  {reads_completed[0]:,} ({reads_completed[0] / operations_completed[0] * 100:.1f}%)")
    print(f"Write operations: {writes_completed[0]:,} ({writes_completed[0] / operations_completed[0] * 100:.1f}%)")
    print(f"Delete operations: {deletes_completed[0]:,} ({deletes_completed[0] / operations_completed[0] * 100:.1f}%)")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Operations per second: {operations_completed[0] / total_time:,.0f}")
    print(f"Final table size: {len(hash_table):,}")
    print(f"Errors encountered: {len(errors)}")

    if errors:
        print("First few errors:")
        for error in errors[:5]:
            print(f"  - {error}")

    # Verify we met our targets
    assert operations_completed[0] >= total_operations, f"Only completed {operations_completed[0]:,} operations"
    assert reads_completed[0] / operations_completed[0] >= 0.75, "Read ratio too low"
    assert len(errors) == 0, f"Encountered {len(errors)} errors"

    print("\n✅ Stress test PASSED!")


def performance_comparison():
    """Compare performance between thread-safe and non-thread-safe versions"""
    print("\n=== PERFORMANCE COMPARISON ===")

    test_cases = [
        (100000, 4, "Small test"),
        (1000000, 8, "Medium test"),
    ]

    for num_ops, num_threads, description in test_cases:
        print(f"\n{description}: {num_ops:,} operations, {num_threads} threads")

        # Thread-safe version
        thread_safe = ThreadSafeHashTable()
        ts_time = run_performance_test(thread_safe, num_ops, num_threads)

        # Non-thread-safe version (single-threaded for comparison)
        non_thread_safe = NonThreadSafeHashTable()
        nts_time = run_performance_test(non_thread_safe, num_ops, 1)

        print(f"  Thread-safe:    {ts_time:.2f}s ({num_ops / ts_time:,.0f} ops/sec)")
        print(f"  Non-thread-safe: {nts_time:.2f}s ({num_ops / nts_time:,.0f} ops/sec)")
        print(f"  Overhead: {((ts_time / nts_time) - 1) * 100:.1f}%")


def run_performance_test(hash_table, num_operations, num_threads):
    """Run performance test on given hash table"""
    # Pre-populate
    for i in range(1000):
        hash_table[f"key_{i}"] = f"value_{i}"

    ops_per_thread = num_operations // num_threads

    def worker(worker_id):
        for i in range(ops_per_thread):
            op_type = random.random()
            if op_type < 0.75:  # Read
                key = f"key_{random.randint(0, 999)}"
                _ = hash_table.get(key, None)
            elif op_type < 0.90:  # Write
                key = f"new_key_{worker_id}_{i}"
                hash_table[key] = f"new_value_{worker_id}_{i}"
            else:  # Delete
                key = f"key_{random.randint(0, 99)}"
                if key in hash_table:
                    del hash_table[key]

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]

    start_time = time.time()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return time.time() - start_time


if __name__ == "__main__":
    # Run the mega stress test
    run_mega_stress_test()

    # Run performance comparison
    performance_comparison()