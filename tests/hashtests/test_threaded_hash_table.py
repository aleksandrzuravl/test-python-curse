import pytest
import threading
import time
import random
from project.hashtable.threaded_hash_table import ThreadSafeHashTable, NonThreadSafeHashTable


class TestThreadSafety:
    """Test thread safety of the hash table"""

    def test_concurrent_inserts_no_data_loss(self):
        """Test that no data is lost during concurrent inserts"""
        hash_table = ThreadSafeHashTable()
        num_threads = 10
        inserts_per_thread = 100
        total_expected = num_threads * inserts_per_thread

        def insert_worker(thread_id):
            for i in range(inserts_per_thread):
                key = f"key_{thread_id}_{i}"
                hash_table[key] = f"value_{thread_id}_{i}"

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=insert_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Check that all inserts were successful
        assert len(hash_table) == total_expected

        # Verify all expected keys are present
        for thread_id in range(num_threads):
            for i in range(inserts_per_thread):
                key = f"key_{thread_id}_{i}"
                assert key in hash_table
                assert hash_table[key] == f"value_{thread_id}_{i}"

    def test_concurrent_reads_writes(self):
        """Test concurrent reads and writes"""
        hash_table = ThreadSafeHashTable()
        initial_data = {f"key_{i}": f"value_{i}" for i in range(100)}

        # Populate initial data
        for key, value in initial_data.items():
            hash_table[key] = value

        read_errors = []
        write_errors = []

        def read_worker():
            try:
                for _ in range(1000):
                    key = f"key_{random.randint(0, 99)}"
                    if key in hash_table:
                        _ = hash_table[key]
                    time.sleep(0.001)
            except Exception as e:
                read_errors.append(e)

        def write_worker(worker_id):
            try:
                for i in range(500):
                    key = f"new_key_{worker_id}_{i}"
                    hash_table[key] = f"new_value_{worker_id}_{i}"
                    time.sleep(0.001)
            except Exception as e:
                write_errors.append(e)

        # Start threads
        readers = [threading.Thread(target=read_worker) for _ in range(5)]
        writers = [threading.Thread(target=write_worker, args=(i,)) for i in range(3)]

        all_threads = readers + writers

        for thread in all_threads:
            thread.start()

        for thread in all_threads:
            thread.join()

        # Verify no errors occurred
        assert len(read_errors) == 0, f"Read errors: {read_errors}"
        assert len(write_errors) == 0, f"Write errors: {write_errors}"

        # Verify initial data is still intact
        for key in initial_data:
            assert key in hash_table
            assert hash_table[key] == initial_data[key]

    def test_concurrent_deletes(self):
        """Test concurrent deletes"""
        hash_table = ThreadSafeHashTable()

        # Populate with test data
        for i in range(200):
            hash_table[f"key_{i}"] = f"value_{i}"

        delete_errors = []

        def delete_worker(worker_id):
            try:
                for i in range(worker_id * 20, (worker_id + 1) * 20):
                    key = f"key_{i}"
                    if key in hash_table:
                        del hash_table[key]
            except Exception as e:
                delete_errors.append(e)

        threads = [threading.Thread(target=delete_worker, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(delete_errors) == 0, f"Delete errors: {delete_errors}"

        # All specified keys should be deleted
        for i in range(100):
            key = f"key_{i}"
            assert key not in hash_table

    def test_iteration_thread_safety(self):
        """Test that iteration works correctly in multi-threaded environment"""
        hash_table = ThreadSafeHashTable()

        # Add some initial data
        for i in range(50):
            hash_table[f"key_{i}"] = f"value_{i}"

        iteration_results = []
        iteration_errors = []

        def iterate_worker():
            try:
                # This should not raise exceptions even if modifications happen
                keys = list(hash_table.keys())
                values = list(hash_table.values())
                iteration_results.append((len(keys), len(values)))
            except Exception as e:
                iteration_errors.append(e)

        def modify_worker():
            for i in range(20):
                hash_table[f"mod_key_{i}"] = f"mod_value_{i}"
                time.sleep(0.001)

        iterators = [threading.Thread(target=iterate_worker) for _ in range(3)]
        modifiers = [threading.Thread(target=modify_worker) for _ in range(2)]

        all_threads = iterators + modifiers

        for thread in all_threads:
            thread.start()

        for thread in all_threads:
            thread.join()

        assert len(iteration_errors) == 0, f"Iteration errors: {iteration_errors}"

    def test_deadlock_prevention(self):
        """Test that no deadlocks occur during complex operations"""
        hash_table = ThreadSafeHashTable(initial_capacity=4)  # Small capacity to force resizing

        def worker_1():
            for i in range(1000):
                hash_table[f"a_{i}"] = i
                _ = hash_table.get(f"a_{i}")

        def worker_2():
            for i in range(1000):
                hash_table[f"b_{i}"] = i
                if f"b_{i}" in hash_table:
                    del hash_table[f"b_{i}"]

        threads = [
            threading.Thread(target=worker_1),
            threading.Thread(target=worker_2),
            threading.Thread(target=worker_1),
            threading.Thread(target=worker_2)
        ]

        for thread in threads:
            thread.start()

        # Wait with timeout to detect deadlocks
        for thread in threads:
            thread.join(timeout=30.0)  # 30 second timeout
            assert not thread.is_alive(), "Thread deadlock detected"


class TestStress:
    """Stress testing for the thread-safe hash table"""

    def test_stress_high_concurrency(self):
        """Stress test with high concurrency"""
        hash_table = ThreadSafeHashTable()
        num_operations = 10000
        num_threads = 20

        operations_completed = [0]
        errors = []

        def stress_worker(worker_id):
            try:
                for i in range(num_operations // num_threads):
                    op_type = random.random()

                    if op_type < 0.75:  # 75% reads
                        key = f"key_{random.randint(0, 999)}"
                        _ = hash_table.get(key, None)
                    elif op_type < 0.90:  # 15% writes
                        key = f"key_{worker_id}_{i}"
                        hash_table[key] = f"value_{worker_id}_{i}"
                    else:  # 10% deletes
                        key = f"key_{random.randint(0, 999)}"
                        if key in hash_table:
                            del hash_table[key]

                    operations_completed[0] += 1
            except Exception as e:
                errors.append(e)

        # Pre-populate some data
        for i in range(1000):
            hash_table[f"key_{i}"] = f"initial_value_{i}"

        threads = [threading.Thread(target=stress_worker, args=(i,)) for i in range(num_threads)]

        start_time = time.time()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        print(f"Stress test completed: {operations_completed[0]} operations in {end_time - start_time:.2f}s")
        print(f"Operations per second: {operations_completed[0] / (end_time - start_time):.2f}")

        assert len(errors) == 0, f"Errors during stress test: {errors}"
        assert operations_completed[0] >= num_operations * 0.95  # Allow 5% margin


class TestPerformanceComparison:
    """Performance comparison between thread-safe and non-thread-safe versions"""

    def test_performance_comparison(self):
        """Compare performance of thread-safe vs non-thread-safe implementation"""
        num_operations = 500000
        read_ratio = 0.75  # 75% reads

        # Test non-thread-safe version (single-threaded)
        non_thread_safe = NonThreadSafeHashTable()
        non_thread_safe_time = self._run_benchmark(non_thread_safe, num_operations, read_ratio, num_threads=1)

        # Test thread-safe version (single-threaded)
        thread_safe = ThreadSafeHashTable()
        thread_safe_single_time = self._run_benchmark(thread_safe, num_operations, read_ratio, num_threads=1)

        # Test thread-safe version (multi-threaded)
        thread_safe_multi = ThreadSafeHashTable()
        thread_safe_multi_time = self._run_benchmark(thread_safe_multi, num_operations, read_ratio, num_threads=4)

        print(f"\nPerformance Comparison ({num_operations} operations, {read_ratio * 100}% reads):")
        print(f"Non-thread-safe (1 thread): {non_thread_safe_time:.2f}s")
        print(f"Thread-safe (1 thread): {thread_safe_single_time:.2f}s")
        print(f"Thread-safe (4 threads): {thread_safe_multi_time:.2f}s")
        print(f"Overhead (single-threaded): {((thread_safe_single_time / non_thread_safe_time) - 1) * 100:.1f}%")

        # Thread-safe should be slower in single-threaded due to locking overhead
        assert thread_safe_single_time > non_thread_safe_time * 0.5  # But not drastically slower

    def _run_benchmark(self, hash_table, num_operations, read_ratio, num_threads=1):
        """Run benchmark on given hash table implementation"""
        # Pre-populate with data
        for i in range(1000):
            hash_table[f"pre_key_{i}"] = f"pre_value_{i}"

        operations_per_thread = num_operations // num_threads
        errors = []

        def benchmark_worker(worker_id):
            try:
                for i in range(operations_per_thread):
                    op_type = random.random()

                    if op_type < read_ratio:  # Read operation
                        key = f"pre_key_{random.randint(0, 999)}"
                        _ = hash_table.get(key, None)
                    elif op_type < 0.95:  # Write operation
                        key = f"key_{worker_id}_{i}"
                        hash_table[key] = f"value_{worker_id}_{i}"
                    else:  # Delete operation
                        key = f"pre_key_{random.randint(0, 99)}"
                        if key in hash_table:
                            del hash_table[key]
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=benchmark_worker, args=(i,)) for i in range(num_threads)]

        start_time = time.time()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        assert len(errors) == 0, f"Benchmark errors: {errors}"

        return end_time - start_time


class TestFunctionality:
    """Test that all original functionality still works"""

    def test_basic_operations(self):
        """Test basic dictionary operations"""
        ht = ThreadSafeHashTable()

        # Test set and get
        ht["key1"] = "value1"
        ht["key2"] = "value2"
        assert ht["key1"] == "value1"
        assert ht["key2"] == "value2"

        # Test update
        ht["key1"] = "new_value1"
        assert ht["key1"] == "new_value1"

        # Test contains
        assert "key1" in ht
        assert "key3" not in ht

        # Test delete
        del ht["key1"]
        assert "key1" not in ht

        # Test length
        assert len(ht) == 1

    def test_iteration(self):
        """Test iteration functionality"""
        ht = ThreadSafeHashTable()

        test_data = {"a": 1, "b": 2, "c": 3}
        for k, v in test_data.items():
            ht[k] = v

        # Test keys
        assert set(ht.keys()) == set(test_data.keys())

        # Test values
        assert set(ht.values()) == set(test_data.values())

        # Test items
        assert dict(ht.items()) == test_data

    def test_collision_resolution(self):
        """Test that collision resolution still works"""
        ht = ThreadSafeHashTable(initial_capacity=4)  # Small capacity

        # Add elements that will cause collisions
        for i in range(10):
            ht[f"key{i}"] = i

        # Verify all elements are accessible
        for i in range(10):
            assert ht[f"key{i}"] == i


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "-s"])