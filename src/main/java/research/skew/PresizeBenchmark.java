package research.skew;

import java.util.Map;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

/**
 * E0: does giving groupingByConcurrent a pre-sized ConcurrentHashMap remove the
 * input-order-dependent slowdowns of the LongAdder control (결과분석표 11절)?
 * Separate class so AggregationBenchmark (4 methods) and run.sh defaults stay unchanged.
 * Run with run_e0.sh; the defaults below are overridden there with -p.
 */
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(value = 3, jvmArgsAppend = {"-Xms512m", "-Xmx512m",
        "-Djava.util.concurrent.ForkJoinPool.common.parallelism=3"})
@Threads(1)
public class PresizeBenchmark {
    @Param({"100000"})
    public int size;

    @Param({"2048"})
    public int cardinality;

    @Param({"hot90"})
    public String distribution;

    @Param({"20260929"})
    public long seed;

    private Workload.Key[] input;
    private int capacity;

    @Setup(Level.Trial)
    public void setup() {
        Workload.Input generated = Workload.generate(size, cardinality, distribution, seed);
        Workload.validate(generated);
        input = generated.keys();
        capacity = Workload.presizedCapacity(cardinality);
        System.out.printf("Input: n=%d, keys=%d, presizedCapacity=%d, poolParallelism=%d, availableProcessors=%d%n",
                size, cardinality, capacity,
                ForkJoinPool.getCommonPoolParallelism(), Runtime.getRuntime().availableProcessors());
    }

    /** Same as AggregationBenchmark.parallelConcurrentAdder, re-measured in the same session. */
    @Benchmark
    public Map<Workload.Key, Long> adderDefault() {
        return Workload.parallelConcurrentAdder(input);
    }

    @Benchmark
    public Map<Workload.Key, Long> adderPresized() {
        return Workload.parallelConcurrentAdderPresized(input, capacity);
    }

    /** Same as AggregationBenchmark.parallelConcurrent (stock counting()). */
    @Benchmark
    public Map<Workload.Key, Long> concurrentDefault() {
        return Workload.parallelConcurrent(input);
    }

    @Benchmark
    public Map<Workload.Key, Long> concurrentPresized() {
        return Workload.parallelConcurrentPresized(input, capacity);
    }
}
