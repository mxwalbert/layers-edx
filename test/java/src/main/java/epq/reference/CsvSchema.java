package epq.reference;

import java.util.List;

public record CsvSchema(List<CsvColumn> columns) {

  public CsvSchema(CsvColumn... columns) {
    this(List.of(columns));
  }

  public CsvSchema {
    columns = List.copyOf(columns);
  }

  public String[] header() {
    return columns.stream()
        .map(CsvColumn::name)
        .toArray(String[]::new);
  }
}
