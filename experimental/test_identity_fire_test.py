"""
Fase 5.2 — Identity Fire Test (prueba de fuego adversarial).

Objetivo explicito: intentar demostrar que la hipotesis de
docs/IDENTITY_ARCHITECTURE.md es FALSA. Si algun test exigiera
modificar container_v1.py (el Core experimental), la hipotesis cae.

No se modifica container_v1.py. No se modifica ipv7_mvp/.

Ver docs/IDENTITY_FIRE_TEST.md para el analisis conceptual caso por
caso (A-P) y el veredicto final.
"""

import unittest
from typing import Set

from .container_v1 import ContainerV1, ContainerError
from . import identity_scenarios as scenarios


class IdentityRoundTripTests(unittest.TestCase):
    """Cada escenario de identidad debe sobrevivir encode(decode(X)) == X
    usando exclusivamente el Core de Fase 4 (ContainerV1/ObjectV1)."""

    def test_all_scenarios_roundtrip(self):
        for name, gen in scenarios.ALL_SCENARIOS:
            with self.subTest(name=name):
                original = gen()
                container = ContainerV1.decode(original)
                self.assertEqual(container.encode(), original)

    def test_replay_pair_is_byte_identical(self):
        """Caso N: el 'replay' no es distinguible del original a nivel de bytes."""
        original, replay = scenarios.case_n_replay_pair()
        self.assertEqual(original, replay)

        decoded_original = ContainerV1.decode(original)
        decoded_replay = ContainerV1.decode(replay)

        # El Core no tiene forma de distinguirlos: son estructuralmente
        # iguales. Esto no es un bug: es la prueba de que el Core no
        # debe (ni puede) resolver replay por si mismo.
        self.assertEqual(decoded_original.encode(), decoded_replay.encode())


class IdentityUnknownTypeTests(unittest.TestCase):
    """Caso B: TYPE de identidad desconocido para el receptor."""

    def test_unknown_identity_type_skipped_not_invalid(self):
        raw = scenarios.case_b_unknown_identity_type()
        container = ContainerV1.decode(raw)

        known_to_receiver: Set[int] = {scenarios.TYPE_CONTACT}
        known = [o for o in container.objects if o.type in known_to_receiver]
        unknown = [o for o in container.objects if o.type not in known_to_receiver]

        self.assertEqual(len(known), 1)
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0].type, 0xE1)

        # El receptor jamas interpreto el VALUE del objeto de identidad
        # futura, pero puede re-emitir el Container intacto.
        self.assertEqual(container.encode(), raw)


class IdentityBlindRelayTests(unittest.TestCase):
    """
    Prueba definitiva (Seccion 4 de IDENTITY_FIRE_TEST.md): un relay
    que no conoce NINGUN TYPE de identidad debe poder transportarla
    byte-a-byte, exactamente igual que en Fase 4.7.
    """

    RELAY_CASES = [
        "A_identity_presented",
        "D_verified_with_evidence",
        "G_rotation",
        "H_revocation",
        "I_delegation",
        "O_binding_conflict",
        "P_duplicate_id",
    ]

    def test_relay_blind_to_identity_semantics(self):
        by_name = dict(scenarios.ALL_SCENARIOS)
        # B (nodo intermedio) no conoce ningun TYPE de identidad.
        known_to_relay: Set[int] = set()

        for name in self.RELAY_CASES:
            with self.subTest(name=name):
                from_a = by_name[name]()

                # B recibe y parsea solo estructura.
                at_b = ContainerV1.decode(from_a)
                self.assertEqual(
                    len([o for o in at_b.objects if o.type in known_to_relay]),
                    0,
                    "B no deberia reconocer ningun TYPE de identidad"
                )

                # B reenvia sin interpretar VALUE.
                to_c = at_b.encode()
                self.assertEqual(to_c, from_a)

                # C recibe exactamente lo que A produjo.
                at_c = ContainerV1.decode(to_c)
                self.assertEqual(at_c.encode(), from_a)


class IdentityCriticalCasesTests(unittest.TestCase):
    """Casos P y O: limites explicitos que no rompen el Core pero
    exigen disciplina de Profile (I-17)."""

    def test_duplicate_id_is_structurally_valid_but_semantically_ambiguous(self):
        """
        Caso P: el Core acepta el Container (I-17: unicidad de ID es
        responsabilidad del Profile, no del Core).
        """
        raw = scenarios.case_p_duplicate_id()
        container = ContainerV1.decode(raw)  # no debe lanzar ContainerError

        ids = [o.id for o in container.objects]
        self.assertEqual(ids.count(7), 2)  # ID duplicado, aceptado por el Core

        # A nivel de Profile: intentar resolver "ref:07" es ambiguo.
        candidates = [o for o in container.objects if o.id == 7]
        self.assertEqual(len(candidates), 2)
        # No hay forma estructural de elegir uno; esto documenta la
        # ambiguedad, no la resuelve (por diseno, I-17).
        self.assertNotEqual(candidates[0].value, candidates[1].value)

    def test_binding_conflict_does_not_break_core(self):
        """Caso O: Evidence y Revocation contradictorias no son un error del Core."""
        raw = scenarios.case_o_binding_conflict()
        container = ContainerV1.decode(raw)  # no debe lanzar ContainerError
        self.assertEqual(container.encode(), raw)


class IdentityMaliciousObjectTests(unittest.TestCase):
    """
    Caso M: un Object de identidad corrupto se rechaza con el mismo
    mecanismo generico de Fase 4.7, sin ningun codigo especifico de
    Identity en el Core.
    """

    def test_oversized_length_rejected(self):
        # Container header: version, flags, count=1, payload_length=6
        # Object: TYPE=20 (identity), ID=1, LENGTH=0xFFFF, solo 2 bytes de value.
        raw = bytes.fromhex("01 00 01 00 06 14 01 ff ff 58 59".replace(" ", ""))
        with self.assertRaises(ContainerError):
            ContainerV1.decode(raw)


if __name__ == "__main__":
    unittest.main()
