package research.skew;

import java.util.Map;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(value = 3, jvmArgsAppend = {"-Xms512m", "-Xmx512m",
        "-Djava.util.concurrent.ForkJoinPool.common.parallelism=3"})
@Threads(1)
public class AggregationBenchmark {
    @Param({"10000", "100000", "1000000"})
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
        System.out.printf("Input: n=%d, keys=%d, observedHotFraction=%.6f, poolParallelism=%d, availableProcessors=%d%n",
                size, cardinality, (double) generated.expected()[0] / size,
                ForkJoinPool.getCommonPoolParallelism(), Runtime.getRuntime().availableProcessors());
    }

    @Benchmark
    public Map<Workload.Key, Long> sequential() {
        return Workload.sequential(input);
    }

    @Benchmark
    public Map<Workload.Key, Long> parallelMerge() {
        return Workload.parallelMerge(input);
    }

    @Benchmark
    public Map<Workload.Key, Long> parallelConcurrent() {
        return Workload.parallelConcurrent(input);
    }
}
