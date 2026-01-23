package epq.reference;

import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public final class CsvRowBuilder {
    private final CsvSchema schema;
    private final Map<String, Object> values = new HashMap<>();

    public CsvRowBuilder(CsvSchema schema) {
        this.schema = schema;
    }

    public CsvRowBuilder set(String column, Object value) {
        CsvColumn col = schema.columns().stream()
                .filter(c -> c.name().equals(column))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown column: " + column));

        if (value == null && !col.nullable()) {
            throw new IllegalStateException(
                    "Column " + column + " is not nullable");
        }

        values.put(column, value);
        return this;
    }

    public String[] buildRow() {
        String[] row = new String[schema.columns().size()];

        for (int i = 0; i < schema.columns().size(); i++) {
            CsvColumn col = schema.columns().get(i);
            Object value = values.get(col.name());

            if (value == null && !col.nullable()) {
                throw new IllegalStateException(
                        "Missing value for column: " + col.name());
            }

            row[i] = serialize(value, col.type());
        }

        return row;
    }

    private String serialize(Object value, CsvColumn.Type type) {
        if (value == null) {
            return "";
        }

        return switch (type) {
            case STRING -> value.toString();
            case INT -> Integer.toString((Integer) value);
            case DOUBLE -> String.format(Locale.ROOT, "%.12e", (Double) value);
            case BOOL -> Boolean.toString((Boolean) value);
        };
    }
}
