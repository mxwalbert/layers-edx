package epq.reference;

public record CsvColumn(
    String name,
    Type type,
    boolean nullable) {
  public enum Type {
    STRING,
    INT,
    DOUBLE,
    BOOL
  }
}
