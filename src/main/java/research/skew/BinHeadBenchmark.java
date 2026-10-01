package research.skew;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.LongAdder;
import java.util.function.Function;
import org.openjdk.jmh.annotations.*;

/**
 * E3 (AstraReview2 5.3): mechanism microbenchmark, separate from the aggregation benchmarks.
 * One pre-built ConcurrentHashMap with exactly two keys in the same bin and no resize:
 * hot Key(0) (90% of records) and cold Key(32) (10%). Only the position of the hot key in
 * bin 0 changes (position=head: [0, 32], position=second: [32, 0]); map capacity, keys,
 * frequencies, threads and counters are the same.
 *   computeIfAbsent(): first-node check succeeds only for position=head; otherwise
 *                      the lookup runs inside synchronized(bin head).
 *   get():             no bin lock in either position (valid here because both keys exist).
 * The increment runs after the lookup in both paths, outside any bin lock.
 * Setup and teardown verify table length, bin-0 order and the final counts.
 */
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(value = 3, jvmArgsAppend = {"-Xms512m", "-Xmx512m",
        "-Djava.util.concurrent.ForkJoinPool.common.parallelism=3",
        "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED"})
@Threads(1)
public class BinHeadBenchmark {
    // new ConcurrentHashMap<>(16) -> tableSizeFor(16 + 8 + 1) = 32 bins; spread(32) & 31 == 0.
    static final int INITIAL_CAPACITY = 16;
    static final int TABLE_LENGTH = 32;
    static final Function<Workload.Key, LongAdder> NEW_ADDER = k -> new LongAdder();

    @Param({"100000"})
    public int size;

    @Param({"head", "second"})
    public String position;

    // Fixed; present so the CSV converter sees the same parameters as the other benchmarks.
    @Param({"2"})
    public int cardinality;

    @Param({"hot90"})
    public String distribution;

    @Param({"20260929"})
    public long seed;

    private final Workload.Key hot = new Workload.Key(0);
    private final Workload.Key cold = new Workload.Key(TABLE_LENGTH);
    private Workload.Key[] input;
    private ConcurrentHashMap<Workload.Key, LongAdder> map;
    private long operations;

    @Setup(Level.Trial)
    public void setup() throws Exception {
        // Same exact-count shuffled order as the main benchmarks (K=2, hot90), keys remapped.
        if (cardinality != 2) throw new IllegalArgumentException("BinHeadBenchmark uses exactly two keys");
        Workload.Key[] generated = Workload.generate(size, cardinality, distribution, seed).keys();
        input = new Workload.Key[generated.length];
        for (int i = 0; i < generated.length; i++) input[i] = generated[i].id() == 0 ? hot : cold;

        map = new ConcurrentHashMap<>(INITIAL_CAPACITY);
        if (position.equals("head")) {
            map.put(hot, new LongAdder());
            map.put(cold, new LongAdder());
        } else if (position.equals("second")) {
            map.put(cold, new LongAdder());
            map.put(hot, new LongAdder());
        } else {
            throw new IllegalArgumentException("position must be head or second: " + position);
        }
        List<Integer> bin0 = bin0Ids();
        List<Integer> want = position.equals("head") ? List.of(0, TABLE_LENGTH) : List.of(TABLE_LENGTH, 0);
        if (tableLength() != TABLE_LENGTH || !bin0.equals(want)) {
            throw new IllegalStateException("unexpected layout: table=" + tableLength() + " bin0=" + bin0);
        }
        operations = 0;
        System.out.printf("Layout: position=%s table=%d bin0=%s poolParallelism=%d%n",
                position, tableLength(), bin0, ForkJoinPool.getCommonPoolParallelism());
    }

    @TearDown(Level.Trial)
    public void verify() throws Exception {
        long expected = operations * size;
        long actual = map.get(hot).sum() + map.get(cold).sum();
        if (map.size() != 2 || actual != expected || tableLength() != TABLE_LENGTH) {
            throw new IllegalStateException("verification failed: size=" + map.size()
                    + " sum=" + actual + " expected=" + expected + " table=" + tableLength());
        }
        System.out.printf("Verify: position=%s table=%d bin0=%s ops=%d sum=%d OK%n",
                position, tableLength(), bin0Ids(), operations, actual);
    }

    @Benchmark
    public ConcurrentHashMap<Workload.Key, LongAdder> computeIfAbsent() {
        operations++;
        Arrays.stream(input).parallel().forEach(k -> map.computeIfAbsent(k, NEW_ADDER).increment());
        return map;
    }

    @Benchmark
    public ConcurrentHashMap<Workload.Key, LongAdder> get() {
        operations++;
        Arrays.stream(input).parallel().forEach(k -> map.get(k).increment());
        return map;
    }

    private int tableLength() throws Exception {
        Object[] table = (Object[]) tableField().get(map);
        return table == null ? 0 : table.length;
    }

    private List<Integer> bin0Ids() throws Exception {
        Class<?> node = Class.forName("java.util.concurrent.ConcurrentHashMap$Node");
        Field key = node.getDeclaredField("key");
        Field next = node.getDeclaredField("next");
        key.setAccessible(true);
        next.setAccessible(true);
        List<Integer> ids = new ArrayList<>();
        for (Object f = ((Object[]) tableField().get(map))[0]; f != null; f = next.get(f)) {
            ids.add(((Workload.Key) key.get(f)).id());
        }
        return ids;
    }

    private static Field tableField() throws Exception {
        Field table = ConcurrentHashMap.class.getDeclaredField("table");
        table.setAccessible(true);
        return table;
    }
}
