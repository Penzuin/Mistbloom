import dev.mistbloom.mistcam.*;
import java.nio.file.*; import java.util.*;
/** Reads shots.txt (MistCam scene lines) and prints every baked frame: name i x y z yaw pitch. */
public class Bake {
  public static void main(String[] a) throws Exception {
    Scene cur = null; List<Scene> all = new ArrayList<>();
    for (String line : Files.readAllLines(Path.of(a[0]))) {
      String[] p = line.trim().split("\\s+");
      if (p[0].equals("scene")) { cur = new Scene(p[1], "world"); cur.closed = p[2].equals("true"); all.add(cur);
        if (p.length > 3) cur.lookAt = new double[]{Double.parseDouble(p[3]), Double.parseDouble(p[4]), Double.parseDouble(p[5])}; }
      else if (p[0].equals("pt")) cur.points.add(Keyframe.parse(line.substring(3)));
    }
    StringBuilder sb = new StringBuilder();
    for (Scene s : all) { List<double[]> f = PathBaker.bake(s);
      for (int i = 0; i < f.size(); i++) { double[] q = f.get(i);
        sb.append(s.name).append(' ').append(i).append(' ').append(q[0]).append(' ').append(q[1]).append(' ').append(q[2]).append(' ').append(q[3]).append(' ').append(q[4]).append('\n'); } }
    Files.writeString(Path.of(a[1]), sb.toString());
  }
}
