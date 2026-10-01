package research.skew;

import java.util.Map;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

/**
 * E1: 2x2 control for the shared-map (groupingByConcurrent) skew cost.
 *   factor 1: per-key synchronized block (downstream not CONCURRENT) present / absent
 *   factor 2: counter layout, single cell (long / AtomicLong) / striped (LongAdder)
 * Separate class so AggregationBenchmark (4 methods) and run.sh defaults stay unchanged.
 * Run with run_e1.sh; the defaults below are overridden there with -p.
 */
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(value = 3, jvmArgsAppend = {"-Xms512m", "-Xmx512m",
        "-Djava.util.concurrent.ForkJoinPool.common.parallelism=3"})
@Threads(1)
public class ControlBenchmark {
    @Param({"100000"})
    public int size;

    @Param({"256"})
    public int cardinality;

    @Param({"uniform", "hot50", "hot90"})
    public String distribution;

    @Param({"20260929"})
    public long seed;

    private Workload.Key[] input;

    @Setup(Level.Trial)
    public void setup() {
        Workload.Input generated = Workload.generate(size, cardinality, distribution, seed);
        Workload.validate(generated);
        input = generated.keys();
        System.out.printf("Input: n=%d, keys=%d, poolParallelism=%d, availableProcessors=%d%n",
                size, cardinality, ForkJoinPool.getCommonPoolParallelism(), Runtime.getRuntime().availableProcessors());
    }

    /** synchronized + single cell: stock counting() (= AggregationBenchmark.parallelConcurrent). */
    @Benchmark
    public Map<Workload.Key, Long> syncLong() {
        return Workload.parallelConcurrent(input);
    }

    /** synchronized + striped: LongAdder downstream without CONCURRENT. */
    @Benchmark
    public Map<Workload.Key, Long> syncAdder() {
        return Workload.parallelConcurrentSyncAdder(input);
    }

    /** synchronized + AtomicLong: same accumulator as casAtomic, CONCURRENT removed (AstraReview2 5.2). */
    @Benchmark
    public Map<Workload.Key, Long> syncAtomic() {
        return Workload.parallelConcurrentSyncAtomic(input);
    }

    /** no per-key lock + single cell: CONCURRENT AtomicLong downstream. */
    @Benchmark
    public Map<Workload.Key, Long> casAtomic() {
        return Workload.parallelConcurrentAtomic(input);
    }

    /** no per-key lock + striped: CONCURRENT LongAdder downstream (= parallelConcurrentAdder). */
    @Benchmark
    public Map<Workload.Key, Long> casAdder() {
        return Workload.parallelConcurrentAdder(input);
    }
}
