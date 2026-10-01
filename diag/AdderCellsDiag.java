import research.skew.Workload;
import research.skew.Workload.Key;
import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/**
 * Diagnostic only (no timing), AstraReview2 5.2: does the hot key's LongAdder actually stripe?
 * LongAdder creates its cells array only after a contended CAS on base. Runs the two LongAdder
 * cells of E1 with the same parallel structure and reports the hot key's cells length:
 *   syncAdder  per-key synchronized around increment() (downstream not CONCURRENT)
 *   casAdder   no per-key synchronized (CONCURRENT downstream)
 * cells = 0 means the adder never left its single base field (no striping).
 */
public class AdderCellsDiag {
    public static void main(String[] a) throws Exception {
        Class<?> striped = Class.forName("java.util.concurrent.atomic.Striped64");
        Field cells = striped.getDeclaredField("cells");
        cells.setAccessible(true);
        int[][] conds = {{100000, 256}, {1000000, 256}};
        String[] dists = {"uniform", "hot50", "hot90"};
        int runs = 5;
        System.out.println("# LongAdder cells of the hot key (Key 0), " + runs + " parallel runs each, pool parallelism "
                + java.util.concurrent.ForkJoinPool.getCommonPoolParallelism() + "\n");
        System.out.println("| N | K | distribution | syncAdder cells per run | casAdder cells per run |");
        System.out.println("|---|---|---|---|---|");
        for (int[] c : conds) for (String d : dists) {
            Key[] keys = Workload.generate(c[0], c[1], d, 20260929L).keys();
            Key hot = null;
            for (Key k : keys) if (k.id() == 0) { hot = k; break; }
            StringBuilder sync = new StringBuilder(), cas = new StringBuilder();
            for (int r = 0; r < runs; r++) {
                ConcurrentHashMap<Key, LongAdder> m1 = new ConcurrentHashMap<>();
                Arrays.stream(keys).parallel().forEach(k -> {
                    LongAdder adder = m1.computeIfAbsent(k, x -> new LongAdder());
                    synchronized (adder) { adder.increment(); }     // what groupingByConcurrent does without CONCURRENT
                });
                ConcurrentHashMap<Key, LongAdder> m2 = new ConcurrentHashMap<>();
                Arrays.stream(keys).parallel().forEach(k -> m2.computeIfAbsent(k, x -> new LongAdder()).increment());
                if (m1.get(hot).sum() != m2.get(hot).sum()) throw new AssertionError("count mismatch");
                Object[] c1 = (Object[]) cells.get(m1.get(hot)), c2 = (Object[]) cells.get(m2.get(hot));
                sync.append(r > 0 ? "/" : "").append(c1 == null ? 0 : c1.length);
                cas.append(r > 0 ? "/" : "").append(c2 == null ? 0 : c2.length);
            }
            System.out.printf("| %,d | %d | %s | %s | %s |%n", c[0], c[1], d, sync, cas);
        }
    }
}
