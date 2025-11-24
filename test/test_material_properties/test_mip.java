import gov.nist.microanalysis.EPQLibrary.*;
import java.util.*;

/**
 * EPQ reference implementation for MIP (Mean Ionization Potential) validation
 * Outputs JSON to stdout for Python test comparison
 */
public class test_mip {
    public static void main(String[] args) {
        // Test 1: MIP for individual elements
        Element[] elements = { Element.Si, Element.O, Element.Fe, Element.Au };
        List<Double> mipValues = new ArrayList<>();

        MeanIonizationPotential mipAlgo = MeanIonizationPotential.Berger83;
        for (Element el : elements) {
            Composition comp = new Composition(el);
            double mip = mipAlgo.computeLn(comp);
            mipValues.add(mip / ToSI.eV(1.0)); // Convert J to eV
        }

        // Test 2: MIP for SiO2 composition
        Composition sio2 = new Composition();
        sio2.addElement(Element.Si, 0.467); // weight fraction
        sio2.addElement(Element.O, 0.533);
        double sio2_mip = mipAlgo.computeLn(sio2) / ToSI.eV(1.0);

        // Output as simple JSON
        System.out.println("{");

        // Element MIPs array
        System.out.print("  \"element_mips\": [");
        for (int i = 0; i < mipValues.size(); i++) {
            System.out.print(mipValues.get(i));
            if (i < mipValues.size() - 1)
                System.out.print(", ");
        }
        System.out.println("],");

        // Element names for reference
        System.out.print("  \"elements\": [");
        for (int i = 0; i < elements.length; i++) {
            System.out.print("\"" + elements[i].toAbbrev() + "\"");
            if (i < elements.length - 1)
                System.out.print(", ");
        }
        System.out.println("],");

        // SiO2 MIP
        System.out.println("  \"sio2_mip\": " + sio2_mip);

        System.out.println("}");
    }
}
