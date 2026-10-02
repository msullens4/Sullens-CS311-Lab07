"""
Lab 7: The Collision Resolver -- starter.

Complete the three classes below. See
Lab_07_The_Collision_Resolver.md, Part B, for the full requirements.
"""

from typing import Generic, Hashable, List, Optional, Tuple, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_TOMBSTONE = object()  # sentinel marking a deleted open-addressing slot


class _ChainNode(Generic[K, V]):
    __slots__ = ("key", "value", "next")

    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value
        self.next: Optional["_ChainNode[K, V]"] = None


class ChainedHashMap(Generic[K, V]):
    """Separate chaining: each bucket is a linked list of (key, value)."""

    def __init__(self, initial_size: int = 16) -> None:
        self._buckets: List[Optional[_ChainNode[K, V]]] = [None] * initial_size
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def insert(self, key: K, value: V) -> None:
        """Insert, or update in place if `key` already exists. Resize (double + rehash) once load factor > 0.75."""
        # TODO
        index = hash(key) % len(self._buckets)

        current = self._buckets[index]

        while current is not None:
            if current.key == key:
                current.value = value
                return 
            current = current.next

        new_node = _ChainNode(key, value)
        new_node.next = self._buckets[index]
        self._buckets[index] = new_node
        self._count += 1 

        if self._count / len(self._buckets) > 0.75:
            self._resize(len(self._buckets) * 2)


    def get(self, key: K) -> V:
        """Return the value for `key`. Raise KeyError if missing."""
        # TODO
        index = hash(key) % len(self._buckets)
        current = self._buckets[index]

        while current is not None:
            if current.key == key:
                return current.value
            current = current.next

        raise KeyError(key)
    
    def delete(self, key: K) -> None:
        """Remove `key`. Raise KeyError if missing."""
        # TODO
        index = hash(key) % len(self._buckets)

        current = self._buckets[index]
        previous = None

        while current is not None:
            if current.key == key:
                if previous is None:
                    self._buckets[index] = current.next
                else:
                    previous.next = current.next

                self._count -= 1
                return 

            previous = current 
            current = current.next

        raise KeyError(key)

    def _resize(self, new_size: int) -> None:
       

        old_buckets = self._buckets
        self._buckets = [None] * new_size

        for head in old_buckets:
            current = head

            while current is not None:
                next_node = current.next

                index = hash(current.key) % new_size

                current.next = self._buckets[index]
                self._buckets[index] = current

                current = next_node



class LinearProbingHashMap(Generic[K, V]):
    """Open addressing with linear probing and tombstone deletion."""

    def __init__(self, initial_size: int = 16) -> None:
        initial_size = self._next_prime(initial_size)

        self._keys: List[object] = [None] * initial_size
        self._values: List[Optional[V]] = [None] * initial_size
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def insert(self, key: K, value: V) -> None:
        """Resize when load factor would exceed 0.7."""

        if (self._count + 1) / len(self._keys) > 0.7:
            self._resize(self._next_prime(len(self._keys) * 2))

        size = len(self._keys)
        start = hash(key) % size
        first_tombstone: Optional[int] = None

        for i in range(size):
            index = (start + i) % size
            current_key = self._keys[index]

            # Empty slot
            if current_key is None:
                if first_tombstone is not None:
                    index = first_tombstone

                self._keys[index] = key
                self._values[index] = value
                self._count += 1
                return

            # Tombstone
            if current_key is _TOMBSTONE:
                if first_tombstone is None:
                    first_tombstone = index
                continue

            # Existing key: update value
            if current_key == key:
                self._values[index] = value
                return

        # If the table has no empty slot but has a tombstone,
        # reuse the tombstone.
        if first_tombstone is not None:
            self._keys[first_tombstone] = key
            self._values[first_tombstone] = value
            self._count += 1
            return

        # Probe sequence was completely full.
        self._resize(self._next_prime(len(self._keys) * 2))
        self.insert(key, value)

    def search(self, key: K) -> V:
        """Return the value for key. Raise KeyError if missing."""

        size = len(self._keys)
        start = hash(key) % size

        for i in range(size):
            index = (start + i) % size
            current_key = self._keys[index]

            # Empty slot means the key cannot appear later.
            if current_key is None:
                raise KeyError(key)

            # Tombstones do not stop the search.
            if current_key is _TOMBSTONE:
                continue

            if current_key == key:
                return self._values[index]  # type: ignore

        raise KeyError(key)

    def delete(self, key: K) -> None:
        """Remove key using a tombstone."""

        size = len(self._keys)
        start = hash(key) % size

        for i in range(size):
            index = (start + i) % size
            current_key = self._keys[index]

            if current_key is None:
                raise KeyError(key)

            if current_key is _TOMBSTONE:
                continue

            if current_key == key:
                self._keys[index] = _TOMBSTONE
                self._values[index] = None
                self._count -= 1
                return

        raise KeyError(key)

    def _resize(self, new_size: int) -> None:
        """Resize and rehash all live entries."""

        new_size = self._next_prime(new_size)

        old_keys = self._keys
        old_values = self._values

        self._keys = [None] * new_size
        self._values = [None] * new_size

        old_count = self._count
        self._count = 0

        for i, key in enumerate(old_keys):
            if key is None or key is _TOMBSTONE:
                continue

            self._insert_without_resize(key, old_values[i])

        self._count = old_count

    def _insert_without_resize(
        self,
        key: object,
        value: Optional[V]
    ) -> None:
        """Insert during resize without triggering another resize."""

        size = len(self._keys)
        start = hash(key) % size

        for i in range(size):
            index = (start + i) % size

            if self._keys[index] is None:
                self._keys[index] = key
                self._values[index] = value
                return

        raise RuntimeError("Hash table is full during resize")

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False

        if n == 2:
            return True

        if n % 2 == 0:
            return False

        divisor = 3

        while divisor * divisor <= n:
            if n % divisor == 0:
                return False

            divisor += 2

        return True

    @classmethod
    def _next_prime(cls, n: int) -> int:
        while not cls._is_prime(n):
            n += 1

        return n


class QuadraticProbingHashMap(Generic[K, V]):
    """
    Open addressing with quadratic probing and tombstone deletion.

    Pitfall to design around: with a power-of-2 table size, the probe
    sequence (idx + i^2) mod size does NOT reach every slot -- it can
    cycle through only about half of them, so the table can appear
    "full" and raise/loop forever even though empty slots exist
    elsewhere. Two standard fixes, pick one:
      (a) use a PRIME table size (so the quadratic sequence covers all
          slots whenever load factor < 1), or
      (b) resize proactively -- check load factor BEFORE attempting an
          insert's probe sequence, not only after a successful insert.
    Using both is safest.
    """

    def __init__(self, initial_size: int = 17) -> None:
        self._keys: List[object] = [None] * initial_size
        self._values: List[Optional[V]] = [None] * initial_size
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def insert(self, key: K, value: V) -> None:
        """Resize (grow + rehash) once load factor > 0.7 -- see the pitfall note above."""
        # TODO
        if (self._count + 1) / len(self._keys) > 0.7:
            self._resize(len(self._keys) * 2)

        size = len(self._keys)
        start = hash(key) % size 

        first_tombstone: Optional[int] = None

        for i in range(size):
            index = (start + i * i) % size 
            current_key = self._keys[index]

            if current_key is None:
                if first_tombstone is not None:
                    index = first_tombstone

                self._keys[index] = key 
                self._values[index] = value
                self._count += 1 
                return 

            if current_key is _TOMBSTONE:
                if first_tombstone is None:
                    first_tombstone = index
                continue

            if current_key == key:
                self._values[index] = value 
                return 

    def search(self, key: K) -> V:
        """Return the value for `key`. Raise KeyError if missing."""
        # TODO
        size = len(self._keys)
        start = hash(key) % size 

        for i in range(size):
            index = (start + i * i) % size
            current_key = self._keys[index]

            if current_key is None:
                raise KeyError(key)

            if current_key is _TOMBSTONE:
                continue

            if current_key == key:
                return self._values[index]
        raise KeyError(key)

    def delete(self, key: K) -> None:
        """Remove `key` using a tombstone. Raise KeyError if missing."""
        # TODO
        size = len(self._keys)
        start = hash(key) % size

        for i in range(size):
            index = (start + i * i) % size
            current_key = self._keys[index]

            if current_key is None:
                raise KeyError(key)

            if current_key is _TOMBSTONE:
                continue

            if current_key == key:
                self._keys[index] = _TOMBSTONE
                self._values[index] = None
                self._count -= 1
                return 
    def _resize(self, new_size: int) -> None:

        new_size = self._next_prime(new_size)

        old_keys = self._keys
        old_values = self._values

        self._keys = [None] * new_size
        self._values = [None] * new_size

        old_count = self._count
        self._count = 0

        for i, key in enumerate(old_keys):
            if key is None or key is _TOMBSTONE:
                continue
            self._insert_without_resize(key, old_values[i])
        self._count = old_count
    def _insert_without_resize(self, key: object, value: Optional[V]) -> None:
       
        size = len(self._keys)
        start = hash(key) % size

        for i in range(size):
            index = (start + i * i) % size

            if self._keys[index] is None:
                self._keys[index] = key
                self._values[index] = value
                return
    def _next_prime(self, n: int) -> int:
        def is_prime(x:int) -> bool:
            if x < 2:
                return False 
            if x % 2 == 0:
                return x == 2
            i = 3
            while i * i <= x:
                if x % 1 == 0:
                    return False
                i += 2
            return True
        while not is_prime(n):
            n += 1 
            return n
            
