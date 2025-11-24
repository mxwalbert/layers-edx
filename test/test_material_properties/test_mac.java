import gov.nist.microanalysis.EPQLibrary.*;
import java.util.*;

/**
 * EPQ reference implementation for MAC validation tests
 * Outputs JSON to stdout for Python test comparison
 */
public class test_mac {
    public static void main(String[] args) {
        // Test 1: Silicon at various energies
        Element si = Element.Si;
        double[] energies = { 1.0, 1.74, 5.0, 10.0, 20.0 }; // keV
        List<Double> macValues = new ArrayList<>();

        for (double energy : energies) {
            double energyJ = ToSI.keV(energy);
            // Use EPQ API - get MAC for element
            double mac = MassAbsorptionCoefficient.Default.compute(si, energyJ);
            macValues.add(mac);
        }

        // Test 2: SiO2 composition at Si Ka energy
        Composition sio2 = new Composition();
        sio2.addElement(si, 0.467); // weight fraction
        sio2.addElement(Element.O, 0.533);

        double energyJ_SiKa = ToSI.keV(1.74);
        double sio2_mac = MassAbsorptionCoefficient.Default.compute(sio2, energyJ_SiKa);

        // Output as simple JSON (no external library needed)
        System.out.println("{");

        // Silicon energies array
        System.out.print("  \"silicon_energies\": [");
        for (int i = 0; i < macValues.size(); i++) {
            System.out.print(macValues.get(i));
            if (i < macValues.size() - 1)
                System.out.print(", ");
        }
        System.out.println("],");

        // SiO2 value
        System.out.println("  \"sio2_at_si_ka\": " + sio2_mac);

        System.out.println("}");
    }
}
