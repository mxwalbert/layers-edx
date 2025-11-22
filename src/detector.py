from layers_edx.element import Element, Composition, Material
from layers_edx.detector.detector import XRayWindowLayer, GridMountedWindow, DetectorProperties, FanoSiLiLineshape, EDSCalibration, DetectorPosition
from layers_edx.detector.eds_detector import EDSDetector

det_window = GridMountedWindow(
    grid_material=Material(Composition([Element('Si')], [1.0]), density=2.33),
    grid_thickness=0.15e6,
    open_fraction=0.78,
    layers=[
        XRayWindowLayer(Material(Composition([Element('Al')], [1.0]), density=2.7), thickness=30.0),
        XRayWindowLayer(Material(Composition([Element('Si'), Element('N')], [3.0, 4.0], False), density=3.17), thickness=40),
    ]
)

det_prop = DetectorProperties(
    channel_count=4096,
    area=30.0,
    thickness=1.0,
    dead_layer=0.03,
    gold_layer=0.0,
    aluminium_layer=10.0,
    nickel_layer=0.0,
    window=det_window
)

det_pos = DetectorPosition(
    elevation=35.0,
    azimuth=0.0,
    sample_distance=30.0,
    optimal_working_distance=8.5
)

det_cal = EDSCalibration(
    channel_width=9.998055346010942,
    zero_offset=2.018306484833711,
    model=FanoSiLiLineshape(
        fwhm_at_mn_ka=129.3
    )
)

detector = EDSDetector(det_prop, det_pos, det_cal)
