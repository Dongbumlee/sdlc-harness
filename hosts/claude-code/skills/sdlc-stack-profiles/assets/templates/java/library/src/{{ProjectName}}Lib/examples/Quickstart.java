import com.example.{{PackageName}}.TextTransforms;

// Runnable quickstart — this is the README example, and CI compiles
// and runs it against the BUILT jar, so the documented usage can
// never drift from what the library actually ships.
public class Quickstart {
  public static void main(String[] args) {
    System.out.println(TextTransforms.slugify("Hello, World!"));
    System.out.println(TextTransforms.truncate("hello world", 8));
  }
}
