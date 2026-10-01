import research.skew.Workload;
import research.skew.Workload.Key;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/**
 * Diagnostic only (no timing). Before each hot-key (Key 0) update of the LongAdder control,
 * reads bin 0 of the ConcurrentHashMap and classifies what it sees:
 *   head        Key(0) is the first node (computeIfAbsent can take its lock-free first-node check)
 *   non_head    another key is the first node of a normal bin (a stable state here makes
 *               computeIfAbsent search under synchronized(first node))
 *   empty       table not initialized yet or bin 0 empty
 *   special     ForwardingNode / ReservationNode / TreeBin (resize or insertion in progress)
 * The observation and the following computeIfAbsent call are NOT atomic, and the probe itself
 * changes scheduling, so the non_head share is an observation rate, not a lock-acquisition rate.
 *
 * Output: one CSV row per run on stdout (raw log), then a Markdown summary on stderr.
 *   java ... BinHeadDiag [hot90] [default|presized] [runs]
 */
public class BinHeadDiag {
    static Field TABLE, NODE_KEY;
    static VarHandle BIN;   // volatile element read, like ConcurrentHashMap.tabAt

    static int classify(ConcurrentHashMap<?, ?> m, Key hot) throws Exception {
        Object tab = TABLE.get(m);
        if (tab == null) return 2;
        Object f = BIN.getVolatile(tab, 0);
        if (f == null) return 2;
        Object k = NODE_KEY.get(f);
        if (k == null) return 3;              // ForwardingNode, ReservationNode, TreeBin have no key
        return k == hot ? 0 : 1;
    }

    public static void main(String[] a) throws Exception {
        TABLE = ConcurrentHashMap.class.getDeclaredField("table");
        TABLE.setAccessible(true);
        Class<?> node = Class.forName("java.util.concurrent.ConcurrentHashMap$Node");
        NODE_KEY = node.getDeclaredField("key");
        NODE_KEY.setAccessible(true);
        BIN = MethodHandles.arrayElementVarHandle(node.arrayType());

        String dist = a.length > 0 ? a[0] : "hot90";
        boolean presized = a.length > 1 && a[1].equals("presized");
        int runs = a.length > 2 ? Integer.parseInt(a[2]) : 5;
        int[][] conds = {{10000, 256}, {100000, 64}, {100000, 256}, {100000, 1024}, {100000, 2048}, {100000, 4096},
                         {100000, 8192}, {1000000, 256}, {1000000, 16384}, {1000000, 32768}, {1000000, 65536}};
        long[] seeds = {20260929L, 20260930L, 20261001L};
        String map = presized ? "presized" : "default";

        System.out.println("map,distribution,size,cardinality,seed,run,hot_updates,head,non_head,empty,special,final_table,bin0_first_id");
        StringBuilder md = new StringBuilder();
        md.append("\n# Bin-head diagnostic (").append(dist).append(", map=").append(map).append(", ")
          .append(runs).append(" parallel runs per row, pool parallelism ")
          .append(java.util.concurrent.ForkJoinPool.getCommonPoolParallelism()).append(")\n\n")
          .append("Non-head observation rate = non_head / hot updates. Not a lock-acquisition rate.\n\n")
          .append("| N | K | seed | non-head % mean (min–max) | runs with non-head ≥ 50% | empty+special % mean | final table lengths |\n")
          .append("|---|---|---|---|---|---|---|\n");
        for (int[] c : conds) for (long s : seeds) {
            if (!Workload.isValid(c[0], c[1])) continue;
            Key[] keys = Workload.generate(c[0], c[1], dist, s).keys();
            Key hot = null;
            for (Key k : keys) if (k.id() == 0) { hot = k; break; }
            final Key H = hot;
            double sum = 0, mn = 101, mx = -1, other = 0;
            int high = 0;
            StringBuilder tables = new StringBuilder();
            for (int r = 1; r <= runs; r++) {
                ConcurrentHashMap<Key, LongAdder> m = presized
                        ? new ConcurrentHashMap<>(Workload.presizedCapacity(c[1])) : new ConcurrentHashMap<>();
                LongAdder[] seen = {new LongAdder(), new LongAdder(), new LongAdder(), new LongAdder()};
                Arrays.stream(keys).parallel().forEach(k -> {
                    if (k == H) {
                        try { seen[classify(m, H)].increment(); } catch (Exception e) { throw new RuntimeException(e); }
                    }
                    m.computeIfAbsent(k, x -> new LongAdder()).increment();
                });
                long total = 0;
                for (LongAdder x : seen) total += x.sum();
                Object[] tab = (Object[]) TABLE.get(m);
                Object first = tab[0] == null ? null : NODE_KEY.get(tab[0]);
                System.out.printf("%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s%n", map, dist, c[0], c[1], s, r, total,
                        seen[0].sum(), seen[1].sum(), seen[2].sum(), seen[3].sum(), tab.length,
                        first instanceof Key k0 ? Integer.toString(k0.id()) : "-");
                double p = 100.0 * seen[1].sum() / total;
                sum += p; mn = Math.min(mn, p); mx = Math.max(mx, p);
                other += 100.0 * (seen[2].sum() + seen[3].sum()) / total;
                if (p >= 50) high++;
                tables.append(r > 1 ? "/" : "").append(tab.length);
            }
            md.append(String.format("| %,d | %d | %d | %.2f (%.2f–%.2f) | %d/%d | %.3f | %s |%n",
                    c[0], c[1], s, sum / runs, mn, mx, high, runs, other / runs, tables));
        }
        System.err.print(md);
    }
}
