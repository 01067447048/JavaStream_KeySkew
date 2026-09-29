package research.skew;

import java.util.Arrays;
import java.util.stream.Collector;
import java.util.stream.Collectors;

public final class Validation {
    public static void main(String[] args) {
        int cases = 0;
        for (int size : new int[]{10_000, 100_000, 1_000_000}) {
            for (int cardinality : new int[]{64, 256, 8192}) {
                // hot90 leaves only 10% of records for the other keys; K=8192 needs N >= 100,000.
                if (cardinality == 8192 && size < 100_000) continue;
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
        System.out.println("PASS: " + cases + " inputs; exact histograms, seed reproducibility, and three collectors agree.");
        System.out.println("This is a correctness check, not a performance measurement.");
    }
}
