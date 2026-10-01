package research.skew;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.SplittableRandom;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;
import java.util.function.Function;
import java.util.stream.Collector;
import java.util.stream.Collectors;

public final class Workload {
    private Workload() {}

    public record Key(int id) {}
    public record Input(Key[] keys, long[] expected) {}

    public static Input generate(int size, int cardinality, String distribution, long seed) {
        if (cardinality < 2 || size < cardinality) {
            throw new IllegalArgumentException("Require size >= cardinality >= 2");
        }
        long[] counts = new long[cardinality];
        if (distribution.equals("uniform")) {
            distribute(counts, 0, size);
        } else {
            double fraction = switch (distribution) {
                case "hot50" -> 0.50;
                case "hot90" -> 0.90;
                default -> throw new IllegalArgumentException("Unknown distribution: " + distribution);
            };
            counts[0] = Math.round(size * fraction);
            int remaining = size - (int) counts[0];
            if (remaining < cardinality - 1) {
                throw new IllegalArgumentException("Too few cold records to preserve cardinality");
            }
            distribute(counts, 1, remaining);
        }
        // Reuse one immutable key object per key; input allocation is outside timing.
        Key[] keys = new Key[size];
        int offset = 0;
        for (int k = 0; k < cardinality; k++) {
            Key key = new Key(k);
            for (long i = 0; i < counts[k]; i++) keys[offset++] = key;
        }
        SplittableRandom random = new SplittableRandom(seed);
        for (int i = keys.length - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            Key tmp = keys[i];
            keys[i] = keys[j];
            keys[j] = tmp;
        }
        return new Input(keys, counts);
    }

    private static void distribute(long[] counts, int start, int total) {
        int groups = counts.length - start;
        for (int k = start; k < counts.length; k++) {
            counts[k] = total / groups + (k - start < total % groups ? 1 : 0);
        }
    }

    public static Map<Key, Long> sequential(Key[] input) {
        return Arrays.stream(input).collect(
                Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }

    public static Map<Key, Long> parallelMerge(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }

    public static Map<Key, Long> parallelConcurrent(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingByConcurrent(Function.identity(), Collectors.counting()));
    }

    // Counting downstream that declares CONCURRENT, so groupingByConcurrent updates
    // it without the per-key synchronized block used for counting() (Collectors.java,
    // JDK 25, lines 1272-1284). Isolates that block as the cause of the skew cost.
    static final Collector<Key, LongAdder, Long> CONCURRENT_COUNTING = Collector.of(
            LongAdder::new,
            (adder, key) -> adder.increment(),
            (left, right) -> { left.add(right.sum()); return left; },
            LongAdder::sum,
            Collector.Characteristics.CONCURRENT, Collector.Characteristics.UNORDERED);

    public static Map<Key, Long> parallelConcurrentAdder(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingByConcurrent(Function.identity(), CONCURRENT_COUNTING));
    }

    // E1 2x2 control: per-key synchronized (downstream not CONCURRENT) x counter layout.
    //   synchronized + single cell : Collectors.counting()     (stock, parallelConcurrent)
    //   synchronized + striped     : SYNC_ADDER_COUNTING       (UNORDERED only -> JDK adds the lock)
    //   no lock      + single cell : ATOMIC_COUNTING           (CONCURRENT, one AtomicLong per key)
    //   no lock      + striped     : CONCURRENT_COUNTING       (the LongAdder control)
    // "no lock" = no per-key synchronized; the ConcurrentHashMap bin lock can still apply (11절).
    static final Collector<Key, LongAdder, Long> SYNC_ADDER_COUNTING = Collector.of(
            LongAdder::new,
            (adder, key) -> adder.increment(),
            (left, right) -> { left.add(right.sum()); return left; },
            LongAdder::sum,
            Collector.Characteristics.UNORDERED);

    static final Collector<Key, AtomicLong, Long> ATOMIC_COUNTING = Collector.of(
            AtomicLong::new,
            (counter, key) -> counter.incrementAndGet(),
            (left, right) -> { left.addAndGet(right.get()); return left; },
            AtomicLong::get,
            Collector.Characteristics.CONCURRENT, Collector.Characteristics.UNORDERED);

    // AstraReview2 5.2: same AtomicLong accumulator as ATOMIC_COUNTING, only CONCURRENT removed,
    // so syncAtomic vs casAtomic changes the per-key synchronized block and nothing else.
    static final Collector<Key, AtomicLong, Long> SYNC_ATOMIC_COUNTING = Collector.of(
            AtomicLong::new,
            (counter, key) -> counter.incrementAndGet(),
            (left, right) -> { left.addAndGet(right.get()); return left; },
            AtomicLong::get,
            Collector.Characteristics.UNORDERED);

    public static Map<Key, Long> parallelConcurrentSyncAtomic(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingByConcurrent(Function.identity(), SYNC_ATOMIC_COUNTING));
    }

    public static Map<Key, Long> parallelConcurrentSyncAdder(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingByConcurrent(Function.identity(), SYNC_ADDER_COUNTING));
    }

    public static Map<Key, Long> parallelConcurrentAtomic(Key[] input) {
        return Arrays.stream(input).parallel().collect(
                Collectors.groupingByConcurrent(Function.identity(), ATOMIC_COUNTING));
    }

    // E0 (결과분석표 11절): with a default-sized map, parallel inserts can leave the table
    // smaller than K, so Key(0) (hash 0) may share bin 0 and sit behind another key; then
    // ConcurrentHashMap.computeIfAbsent skips its lock-free first-node check and locks the bin.
    // new ConcurrentHashMap<>(4K) allocates tableSizeFor(4K + 2K + 1) = 8K bins for K a power
    // of two, so Key(0) is alone in bin 0 and the K keys (< 0.75 * 8K) never trigger a resize.
    public static int presizedCapacity(int cardinality) {
        return 4 * cardinality;
    }

    public static Map<Key, Long> parallelConcurrentPresized(Key[] input, int initialCapacity) {
        return Arrays.stream(input).parallel().collect(Collectors.groupingByConcurrent(
                Function.identity(), () -> new ConcurrentHashMap<>(initialCapacity), Collectors.counting()));
    }

    public static Map<Key, Long> parallelConcurrentAdderPresized(Key[] input, int initialCapacity) {
        return Arrays.stream(input).parallel().collect(Collectors.groupingByConcurrent(
                Function.identity(), () -> new ConcurrentHashMap<>(initialCapacity), CONCURRENT_COUNTING));
    }

    /** Same rule as generate(): every key must appear, even under hot90. */
    public static boolean isValid(int size, int cardinality) {
        return cardinality >= 2 && size >= cardinality
                && size - Math.round(size * 0.90) >= cardinality - 1;
    }

    public static void validate(Input input) {
        // Independent loop checks both the generator and all four collectors.
        long[] actualCounts = new long[input.expected().length];
        for (Key key : input.keys()) actualCounts[key.id()]++;
        if (!Arrays.equals(actualCounts, input.expected())) {
            throw new AssertionError("Input histogram differs from the designed counts");
        }
        Map<Key, Long> expectedMap = new HashMap<>();
        for (int k = 0; k < actualCounts.length; k++) {
            if (actualCounts[k] <= 0) throw new AssertionError("Missing key " + k);
            expectedMap.put(new Key(k), actualCounts[k]);
        }
        if (!expectedMap.equals(sequential(input.keys()))) throw new AssertionError("Sequential mismatch");
        if (!expectedMap.equals(parallelMerge(input.keys()))) throw new AssertionError("Parallel merge mismatch");
        if (!expectedMap.equals(parallelConcurrent(input.keys()))) throw new AssertionError("Concurrent mismatch");
        if (!expectedMap.equals(parallelConcurrentAdder(input.keys()))) throw new AssertionError("Concurrent adder mismatch");
        int capacity = presizedCapacity(actualCounts.length);
        if (!expectedMap.equals(parallelConcurrentPresized(input.keys(), capacity))) throw new AssertionError("Presized concurrent mismatch");
        if (!expectedMap.equals(parallelConcurrentAdderPresized(input.keys(), capacity))) throw new AssertionError("Presized adder mismatch");
        if (!expectedMap.equals(parallelConcurrentSyncAdder(input.keys()))) throw new AssertionError("Synchronized adder mismatch");
        if (!expectedMap.equals(parallelConcurrentAtomic(input.keys()))) throw new AssertionError("Atomic counter mismatch");
        if (!expectedMap.equals(parallelConcurrentSyncAtomic(input.keys()))) throw new AssertionError("Synchronized atomic mismatch");
    }
}
