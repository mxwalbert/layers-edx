import gov.nist.microanalysis.EPQLibrary.*;
import java.util.*;

/**
 * EPQ reference for XRay Transition properties
 */
public class test_xrt {
    public static void main(String[] args) throws Exception {
        // Test: Si Ka transitions
        Element si = Element.Si;
        AtomicShell kShell = new AtomicShell(si, AtomicShell.K);
        XRayTransitionSet transitions = new XRayTransitionSet(kShell);
        List<Map<String, Object>> transitionData = new ArrayList<>();

        for (XRayTransition xrt : transitions) {
            if (xrt.getFamily() == AtomicShell.KFamily) {
                Map<String, Object> data = new HashMap<>();
                data.put("name", xrt.getIUPACName());
                data.put("energy_ev", xrt.getEnergy() / ToSI.eV(1.0));
                data.put("weight", xrt.getWeight(XRayTransition.NormalizeFamily));
                transitionData.add(data);
            }
        }

        // Output JSON
        System.out.println("{");
        System.out.println("  \"element\": \"" + si.toAbbrev() + "\",");
        System.out.print("  \"transitions\": [");
        for (int i = 0; i < transitionData.size(); i++) {
            Map<String, Object> t = transitionData.get(i);
            System.out.print("{");
            System.out.print("\"name\":\"" + t.get("name") + "\",");
            System.out.print("\"energy_ev\":" + t.get("energy_ev") + ",");
            System.out.print("\"weight\":" + t.get("weight"));
            System.out.print("}");
            if (i < transitionData.size() - 1)
                System.out.print(",");
        }
        System.out.println("]");
        System.out.println("}");
    }
}
