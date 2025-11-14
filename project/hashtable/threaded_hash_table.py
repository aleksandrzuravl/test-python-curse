import threading
import time
from collections.abc import MutableMapping
from typing import Any, Optional, Iterator
import random


class Node:
    """Node of doubly linked list for storing key-value pairs"""
    __slots__ = ('key', 'value', 'prev', 'next', 'next_in_bucket')

    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
        self.next_in_bucket = None


class DoublyLinkedList:
    """Doubly linked list for storing elements in one hash table bucket"""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def __len__(self) -> int:
        """Return the number of elements in the list"""
        with self._lock:
            return self._size

    def append(self, key: Any, value: Any) -> Node:
        """Add a new node to the end of the list"""
        with self._lock:
            new_node = Node(key, value)

            if self.head is None:
                self.head = self.tail = new_node
            else:
                new_node.prev = self.tail
                self.tail.next = new_node
                self.tail = new_node

            self._size += 1
            return new_node

    def find(self, key: Any) -> Optional[Node]:
        """Find a node by key in the list"""
        with self._lock:
            current = self.head
            while current:
                if current.key == key:
                    return current
                current = current.next
            return None

    def remove(self, node: Node) -> None:
        """Remove a node from the list"""
        with self._lock:
            if node.prev:
                node.prev.next = node.next
            else:
                self.head = node.next

            if node.next:
                node.next.prev = node.prev
            else:
                self.tail = node.prev

            self._size -= 1

    def __iter__(self):
        """Forward iterator over keys in the list"""
        with self._lock:
            current = self.head
            while current:
                yield current.key
                current = current.next

    def reverse_iter(self):
        """Reverse iterator over keys in the list"""
        with self._lock:
            current = self.tail
            while current:
                yield current.key
                current = current.prev


class ThreadSafeHashTable(MutableMapping):
    """
    Thread-safe hash table with fine-grained locking
    Uses separate locks for each bucket to maximize concurrency
    """

    def __init__(self, initial_capacity: int = 8, load_factor: float = 0.75):
        if initial_capacity <= 0:
            raise ValueError("Initial capacity must be positive")
        if not 0 < load_factor <= 1:
            raise ValueError("Load factor must be between 0 and 1")

        self._capacity = initial_capacity
        self._load_factor = load_factor
        self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]
        self._bucket_locks = [threading.RLock() for _ in range(self._capacity)]  # Separate locks for each bucket
        self._size = 0
        self._keys_list = DoublyLinkedList()
        self._global_lock = threading.RLock()  # For resize operations

    def _hash(self, key: Any) -> int:
        """Calculate hash value for key and return bucket index"""
        return hash(key) % self._capacity

    def _get_bucket_lock(self, key: Any) -> threading.RLock:
        """Get the lock for specific bucket"""
        return self._bucket_locks[self._hash(key)]

    def _resize(self, new_capacity: int) -> None:
        """Resize the hash table - requires global lock"""
        with self._global_lock:
            # Double-check if resize is still needed
            if self._size / self._capacity <= self._load_factor:
                return

            # Acquire all bucket locks to prevent modifications during resize
            for lock in self._bucket_locks:
                lock.acquire()

            try:
                old_buckets = self._buckets
                old_capacity = self._capacity

                self._capacity = new_capacity
                self._buckets = [DoublyLinkedList() for _ in range(new_capacity)]
                self._bucket_locks = [threading.RLock() for _ in range(new_capacity)]
                self._size = 0

                old_keys = list(self._keys_list)
                self._keys_list = DoublyLinkedList()

                # Rehash all elements
                for key in old_keys:
                    for bucket in old_buckets:
                        node = bucket.find(key)
                        if node:
                            self[key] = node.value
                            break
            finally:
                # Release all old bucket locks
                for lock in self._bucket_locks[:old_capacity]:
                    try:
                        lock.release()
                    except RuntimeError:
                        pass

    def _check_resize(self) -> None:
        """Check if resizing is needed"""
        if self._size / self._capacity > self._load_factor:
            self._resize(self._capacity * 2)

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set value for key - thread-safe"""
        bucket_index = self._hash(key)
        bucket_lock = self._bucket_locks[bucket_index]

        with bucket_lock:
            bucket = self._buckets[bucket_index]
            existing_node = bucket.find(key)

            if existing_node:
                existing_node.value = value
                # Update in main list (requires global lock for consistency)
                with self._global_lock:
                    current = self._keys_list.head
                    while current:
                        if current.key == key:
                            current.value = value
                            break
                        current = current.next
            else:
                bucket.append(key, value)
                with self._global_lock:
                    self._keys_list.append(key, value)
                    self._size += 1

        # Check resize outside bucket lock to avoid deadlock
        if not existing_node:
            self._check_resize()

    def __getitem__(self, key: Any) -> Any:
        """Get value for key - thread-safe read"""
        bucket_index = self._hash(key)
        bucket_lock = self._bucket_locks[bucket_index]

        with bucket_lock:
            bucket = self._buckets[bucket_index]
            node = bucket.find(key)
            if node is None:
                raise KeyError(key)
            return node.value

    def get(self, key: Any, default: Any = None) -> Any:
        """Thread-safe get with default value"""
        try:
            return self[key]
        except KeyError:
            return default

    def __delitem__(self, key: Any) -> None:
        """Delete key from hash table - thread-safe"""
        bucket_index = self._hash(key)
        bucket_lock = self._bucket_locks[bucket_index]

        with bucket_lock:
            bucket = self._buckets[bucket_index]
            node = bucket.find(key)
            if node is None:
                raise KeyError(key)

            bucket.remove(node)

            with self._global_lock:
                current = self._keys_list.head
                while current:
                    if current.key == key:
                        self._keys_list.remove(current)
                        break
                    current = current.next

                self._size -= 1

    def __contains__(self, key: Any) -> bool:
        """Check if key exists - thread-safe"""
        bucket_index = self._hash(key)
        bucket_lock = self._bucket_locks[bucket_index]

        with bucket_lock:
            bucket = self._buckets[bucket_index]
            return bucket.find(key) is not None

    def __iter__(self) -> Iterator[Any]:
        """Forward iterator - requires global lock for consistency"""
        with self._global_lock:
            current = self._keys_list.head
            while current:
                yield current.key
                current = current.next

    def __reversed__(self) -> Iterator[Any]:
        """Reverse iterator - requires global lock for consistency"""
        with self._global_lock:
            current = self._keys_list.tail
            while current:
                yield current.key
                current = current.prev

    def __len__(self) -> int:
        """Return number of elements - thread-safe"""
        with self._global_lock:
            return self._size

    def __repr__(self) -> str:
        """String representation - requires global lock"""
        with self._global_lock:
            items = []
            for key in self:
                items.append(f"{key!r}: {self[key]!r}")
            return "{" + ", ".join(items) + "}"

    def keys(self) -> Iterator[Any]:
        """Return keys in insertion order"""
        return iter(self)

    def values(self) -> Iterator[Any]:
        """Return values in insertion order"""
        with self._global_lock:
            current = self._keys_list.head
            while current:
                yield current.value
                current = current.next

    def items(self) -> Iterator[tuple[Any, Any]]:
        """Return key-value pairs in insertion order"""
        with self._global_lock:
            current = self._keys_list.head
            while current:
                yield (current.key, current.value)
                current = current.next

    def clear(self) -> None:
        """Clear all elements - thread-safe"""
        with self._global_lock:
            for bucket_lock in self._bucket_locks:
                bucket_lock.acquire()

            try:
                self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]
                self._keys_list = DoublyLinkedList()
                self._size = 0
            finally:
                for lock in self._bucket_locks:
                    lock.release()


class NonThreadSafeHashTable(MutableMapping):
    """Non-thread-safe version for performance comparison"""

    def __init__(self, initial_capacity: int = 8, load_factor: float = 0.75):
        self._capacity = initial_capacity
        self._load_factor = load_factor
        self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]
        self._size = 0
        self._keys_list = DoublyLinkedList()

    def _hash(self, key: Any) -> int:
        return hash(key) % self._capacity

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [DoublyLinkedList() for _ in range(new_capacity)]
        self._size = 0

        old_keys = list(self._keys_list)
        self._keys_list = DoublyLinkedList()

        for key in old_keys:
            for bucket in old_buckets:
                node = bucket.find(key)
                if node:
                    self[key] = node.value
                    break

    def _check_resize(self) -> None:
        if self._size / self._capacity > self._load_factor:
            self._resize(self._capacity * 2)

    def __setitem__(self, key: Any, value: Any) -> None:
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]

        existing_node = bucket.find(key)
        if existing_node:
            existing_node.value = value
            current = self._keys_list.head
            while current:
                if current.key == key:
                    current.value = value
                    break
                current = current.next
        else:
            bucket.append(key, value)
            self._keys_list.append(key, value)
            self._size += 1
            self._check_resize()

    def __getitem__(self, key: Any) -> Any:
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]

        node = bucket.find(key)
        if node is None:
            raise KeyError(key)
        return node.value

    def __delitem__(self, key: Any) -> None:
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]

        node = bucket.find(key)
        if node is None:
            raise KeyError(key)

        bucket.remove(node)
        current = self._keys_list.head
        while current:
            if current.key == key:
                self._keys_list.remove(current)
                break
            current = current.next

        self._size -= 1

    def __contains__(self, key: Any) -> bool:
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]
        return bucket.find(key) is not None

    def __iter__(self):
        current = self._keys_list.head
        while current:
            yield current.key
            current = current.next

    def __len__(self) -> int:
        return self._size