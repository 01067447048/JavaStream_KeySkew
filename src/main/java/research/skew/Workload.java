package research.skew;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.SplittableRandom;
import java.util.function.Function;
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

    public static void validate(Input input) {
        // Independent loop checks both the generator and all three collectors.
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
    }
}
