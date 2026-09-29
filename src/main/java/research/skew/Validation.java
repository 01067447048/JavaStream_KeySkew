package research.skew;

import java.util.Arrays;
import java.util.stream.Collector;
import java.util.stream.Collectors;

public final class Validation {
    public static void main(String[] args) {
        int cases = 0;
        for (int size : new int[]{10_000, 100_000, 1_000_000}) {
            // 64-8192: main runs; 1024-65536: N/K boundary runs.
            for (int cardinality : new int[]{64, 256, 1024, 2048, 4096, 8192, 16384, 32768, 65536}) {
                // hot90 leaves only 10% of records for the other keys.
                if (!Workload.isValid(size, cardinality)) continue;
                for (String distribution : new String[]{"uniform", "hot50", "hot90"}) {
                    for (long seed : new long[]{20260929L, 20260930L}) {
                        Workload.Input input = Workload.generate(size, cardinality, distribution, seed);
                        Workload.validate(input);
                        Workload.Input repeat = Workload.generate(size, cardinality, distribution, seed);
                        if (!Arrays.equals(input.keys(), repeat.keys())) {
                            throw new AssertionError("Input seed is not reproducible");
                        }
                        cases++;
                    }
                }
            }
        }
        if (Collectors.counting().characteristics().contains(Collector.Characteristics.CONCURRENT)) {
            throw new AssertionError("Revisit synchronization hypothesis for this JDK");
        }
        if (!Workload.CONCURRENT_COUNTING.characteristics().contains(Collector.Characteristics.CONCURRENT)) {
            throw new AssertionError("Adder collector must be CONCURRENT to skip the per-key lock");
        }
        System.out.println("PASS: " + cases + " inputs; exact histograms, seed reproducibility, and four collectors agree.");
        System.out.println("This is a correctness check, not a performance measurement.");
    }
}
