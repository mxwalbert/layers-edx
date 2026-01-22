package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import gov.nist.microanalysis.EPQLibrary.EPQFatalException;
import gov.nist.microanalysis.EPQLibrary.Element;

public final class DumpElement implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("Z", INT, false),
      new CsvColumn("symbol", STRING, false),
      new CsvColumn("name", STRING, false),
      new CsvColumn("atomic_weight", DOUBLE, false),
      new CsvColumn("mass_in_kg", DOUBLE, false),
      new CsvColumn("ionization_energy", DOUBLE, true),
      new CsvColumn("mean_ionization_potential", DOUBLE, false));

  @Override
  public String name() {
    return "Element";
  }

  @Override
  public String usage() {
    return "Element Z=<atomic number>";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);

    final int Z = ctx.getInt("Z", 1, Element.elmEndOfElements - 1);
    final Element element = Element.byAtomicNumber(Z);

    Double ionizationEnergy = null;
    try {
      ionizationEnergy = element.getIonizationEnergy();
    } catch (EPQFatalException e) {
      // Leave as null
    }

    rowBuilder
        .set("Z", Z)
        .set("symbol", element.toAbbrev())
        .set("name", element.toString())
        .set("atomic_weight", element.getAtomicWeight())
        .set("mass_in_kg", element.getMass())
        .set("ionization_energy", ionizationEnergy)
        .set("mean_ionization_potential", element.meanIonizationPotential());

    ctx.row(rowBuilder.buildRow());
    ctx.flush();
  }

}
