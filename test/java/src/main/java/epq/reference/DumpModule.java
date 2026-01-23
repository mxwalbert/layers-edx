package epq.reference;

public interface DumpModule {

  /**
   * The command name used on the CLI (e.g. "XRayTransition").
   */
  String name();

  /**
   * Return usage information for this dump module.
   */
  String usage();

  /**
   * Return the CSV schema.
   */
  CsvSchema schema();

  /**
   * Execute the dump and emit CSV via the DumpContext.
   */
  void run(DumpContext ctx) throws IllegalArgumentException;

}
