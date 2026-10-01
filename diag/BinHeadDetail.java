import research.skew.Workload;
import research.skew.Workload.Key;
import java.lang.reflect.Field;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

public class BinHeadDetail {
    public static void main(String[] a) throws Exception {
        Field TABLE = ConcurrentHashMap.class.getDeclaredField("table"); TABLE.setAccessible(true);
        Class<?> node = Class.forName("java.util.concurrent.ConcurrentHashMap$Node");
        Field KEY = node.getDeclaredField("key"); KEY.setAccessible(true);
        Field NEXT = node.getDeclaredField("next"); NEXT.setAccessible(true);
        int n = Integer.parseInt(a[0]), k = Integer.parseInt(a[1]); long seed = Long.parseLong(a[2]);
        Key[] keys = Workload.generate(n, k, "hot90", seed).keys();
        Key hot = null; for (Key x : keys) if (x.id() == 0) { hot = x; break; }
        final Key H = hot;
        for (int r = 0; r < 6; r++) {
            ConcurrentHashMap<Key, LongAdder> m = new ConcurrentHashMap<>();
            ConcurrentHashMap<String, LongAdder> why = new ConcurrentHashMap<>();
            Arrays.stream(keys).parallel().forEach(x -> {
                if (x == H) try {
                    Object[] tab = (Object[]) TABLE.get(m);
                    Object f = tab == null ? null : tab[0];
                    String c = f == null ? "empty" : KEY.get(f) == H ? "head" : KEY.get(f) == null ? f.getClass().getSimpleName()
                              : "behind key " + ((Key) KEY.get(f)).id() + " (len " + tab.length + ")";
                    why.computeIfAbsent(c, z -> new LongAdder()).increment();
                } catch (Exception e) { throw new RuntimeException(e); }
                m.computeIfAbsent(x, z -> new LongAdder()).increment();
            });
            Object[] tab = (Object[]) TABLE.get(m);
            List<Object> chain = new ArrayList<>();
            for (Object f = tab[0]; f != null; f = NEXT.get(f)) chain.add(KEY.get(f) instanceof Key kk ? kk.id() : KEY.get(f));
            TreeMap<String, Long> w = new TreeMap<>(); why.forEach((s, v) -> w.put(s, v.sum()));
            System.out.println("run " + r + ": final table=" + tab.length + " bin0=" + chain + "  " + w);
        }
    }
}
