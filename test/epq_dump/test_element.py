import pytest
from pytest import approx  # type: ignore
from test.epq_dump.validators import ElementRow
from layers_edx.element import Element


@pytest.mark.epq_ref(module="Element")
@pytest.mark.parametrize(
    "Z",
    range(1, 110),
)
class TestElementProperties:
    @pytest.fixture(autouse=True)
    def setup_element(self, Z: int, java_dump: list[ElementRow]):
        self.element = Element(Z)
        self.ref = java_dump[0]

    def test_atomic_number(self):
        assert self.ref.Z == self.element.atomic_number

    def test_symbol(self):
        assert self.ref.symbol == self.element.name

    def test_atomic_weight(self):
        assert self.ref.atomic_weight == approx(self.element.atomic_weight, rel=1e-3)

    def test_mass_in_kg(self):
        assert self.ref.mass_in_kg == approx(self.element.mass, rel=1e-3)

    def test_ionization_energy(self):
        assert self.ref.ionization_energy == approx(
            self.element.ionization_energy, rel=1e-3
        )

    @pytest.mark.skip(reason="Not implemented yet")
    def test_mean_ionization_potential(self):
        pass
        # assert self.ref.mean_ionization_potential == approx(
        #     self.element.mean_ionization_potential, rel=1e-3
        # )

