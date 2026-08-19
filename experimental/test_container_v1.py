"""
Tests experimentales del wire format V1 de Container/Object.

No toca el Core de ipv7_mvp. Es el juez antes de la integracion.
"""

import unittest
from typing import Set, List

from .container_v1 import ContainerV1, ObjectV1, ContainerError
from . import hex_vectors


class ContainerV1RoundTripTests(unittest.TestCase):
    """Round-trip: encode(decode(X)) == X para todos los vectores V1."""

    def test_hex_vectors_roundtrip(self):
        for name, gen in hex_vectors.HEX_VECTORS:
            with self.subTest(name=name):
                original = gen()
                container = ContainerV1.decode(original)
                encoded = container.encode()
                self.assertEqual(encoded, original)


class ContainerV1UnknownObjectTests(unittest.TestCase):
    """Unknown type != invalid. Preserve and re-serialize."""

    def test_unknown_object_ignored_but_preserved(self):
        raw = hex_vectors.make_unknown_object()
        container = ContainerV1.decode(raw)

        types = [obj.type for obj in container.objects]
        ids = [obj.id for obj in container.objects]
        values = [obj.value for obj in container.objects]

        self.assertEqual(types, [1, 237, 2])
        self.assertEqual(ids, [0, 1, 2])
        self.assertEqual(values, [b"known-1", b"unknown", b"known-2"])

        # Re-serializacion exacta: nunca se interpreto VALUE.
        self.assertEqual(container.encode(), raw)

    def test_known_types_extracted(self):
        """Simula un nodo que conoce tipos 1 y 2, ignora 237."""
        raw = hex_vectors.make_unknown_object()
        container = ContainerV1.decode(raw)
        known: Set[int] = {1, 2}

        known_objects: List[ObjectV1] = [
            obj for obj in container.objects if obj.type in known
        ]
        unknown_objects: List[ObjectV1] = [
            obj for obj in container.objects if obj.type not in known
        ]

        self.assertEqual(len(known_objects), 2)
        self.assertEqual(len(unknown_objects), 1)
        self.assertEqual(unknown_objects[0].type, 237)
        self.assertEqual(container.encode(), raw)


class ContainerV1EdgeCases(unittest.TestCase):
    """Limites y casos de borde V1."""

    def test_empty_container(self):
        """OBJECT_COUNT = 0 debe ser valido."""
        container = ContainerV1()
        raw = container.encode()
        self.assertEqual(raw, bytes.fromhex("01 00 00 00 00"))

        decoded = ContainerV1.decode(raw)
        self.assertEqual(decoded.objects, [])
        self.assertEqual(decoded.object_count, 0)
        self.assertEqual(decoded.payload_length, 0)

    def test_object_length_zero(self):
        """LENGTH = 0 es valido."""
        container = ContainerV1(objects=[ObjectV1(type=1, id=0, value=b"")])
        raw = container.encode()
        decoded = ContainerV1.decode(raw)
        self.assertEqual(decoded.objects[0].value, b"")
        self.assertEqual(decoded.payload_length, 4)

    def test_255_objects(self):
        """OBJECT_COUNT maximo."""
        objects = [ObjectV1(type=1, id=i, value=b"x") for i in range(255)]
        container = ContainerV1(objects=objects)
        raw = container.encode()
        decoded = ContainerV1.decode(raw)
        self.assertEqual(len(decoded.objects), 255)
        self.assertEqual(decoded.encode(), raw)

    def test_65531_byte_value(self):
        """VALUE maximo que cabe en un Container V1 (payload total 65535)."""
        value = b"\x00" * 65531
        container = ContainerV1(objects=[ObjectV1(type=1, id=0, value=value)])
        raw = container.encode()
        decoded = ContainerV1.decode(raw)
        self.assertEqual(decoded.objects[0].value, value)
        self.assertEqual(decoded.payload_length, 65535)
        self.assertEqual(decoded.encode(), raw)


class ContainerV1CorruptionTests(unittest.TestCase):
    """El formato debe detectar corrupcion estructural inequivocamente."""

    def _valid_container(self) -> bytes:
        return ContainerV1(objects=[
            ObjectV1(type=1, id=0, value=b"abc"),
            ObjectV1(type=2, id=1, value=b"de"),
        ]).encode()

    def test_length_too_large(self):
        """LENGTH de un objeto que excede el payload restante."""
        raw = bytearray(self._valid_container())
        # Offset del campo LENGTH del primer objeto: header 5 + TYPE(1) + ID(1) = 7
        raw[7] = 0xFF
        raw[8] = 0xFF
        with self.assertRaises(ContainerError):
            ContainerV1.decode(bytes(raw))

    def test_truncated_value(self):
        """Objeto anuncia mas bytes de los que existen."""
        raw = self._valid_container()
        with self.assertRaises(ContainerError):
            ContainerV1.decode(raw[:-1])

    def test_payload_length_incorrect(self):
        """PAYLOAD_LENGTH no coincide con el tamano real."""
        raw = bytearray(self._valid_container())
        raw[3] = 0x00
        raw[4] = 0x01  # anuncia payload de 1 byte
        with self.assertRaises(ContainerError):
            ContainerV1.decode(bytes(raw))

    def test_object_count_incorrect(self):
        """OBJECT_COUNT no coincide con los objetos parseables."""
        raw = bytearray(self._valid_container())
        raw[2] = 0x05  # dice 5 objetos, solo hay 2
        with self.assertRaises(ContainerError):
            ContainerV1.decode(bytes(raw))

    def test_container_truncated(self):
        """Container cortado a la mitad."""
        raw = self._valid_container()
        with self.assertRaises(ContainerError):
            ContainerV1.decode(raw[:7])

    def test_object_truncated(self):
        """Solo header de un objeto, sin value."""
        raw = self._valid_container()
        with self.assertRaises(ContainerError):
            ContainerV1.decode(raw[:-3])

    def test_id_255_reserved(self):
        """ID = 255 es reservado."""
        container = ContainerV1(objects=[ObjectV1(type=1, id=255, value=b"x")])
        with self.assertRaises(ContainerError):
            container.encode()

    def test_type_0_reserved(self):
        """TYPE = 0 es reservado."""
        with self.assertRaises(ContainerError):
            ContainerV1(objects=[ObjectV1(type=0, id=0, value=b"x")]).encode()

    def test_type_255_reserved(self):
        """TYPE = 255 es reservado."""
        with self.assertRaises(ContainerError):
            ContainerV1(objects=[ObjectV1(type=255, id=0, value=b"x")]).encode()


class ContainerV1RelayTests(unittest.TestCase):
    """Relay transparente: parse estructural, reenvia sin interpretar."""

    def test_relay_unknown_object(self):
        """Nodo B recibe un objeto que no conoce y lo reenvia intacto."""
        original = hex_vectors.make_unknown_object()

        # B recibe y parsea estructuralmente.
        container = ContainerV1.decode(original)

        # B no conoce TYPE 237, pero nunca toco VALUE.
        unknown = [obj for obj in container.objects if obj.type == 237]
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0].value, b"unknown")

        # B reenvia exactamente lo mismo.
        relayed = container.encode()
        self.assertEqual(relayed, original)

    def test_mutant_container_end_to_end(self):
        """
        A -> B -> C. B no entiende 237 ni 242, pero C recibe exactamente
        lo que A produjo.
        """
        from_a = hex_vectors.make_mutant_relay()

        # B: parser estrictamente estructural.
        at_b = ContainerV1.decode(from_a)
        known_to_b: Set[int] = {1, 2}
        known_at_b = [obj for obj in at_b.objects if obj.type in known_to_b]
        unknown_at_b = [obj for obj in at_b.objects if obj.type not in known_to_b]

        self.assertEqual(len(known_at_b), 2)
        self.assertEqual(len(unknown_at_b), 2)

        # B reenvia.
        to_c = at_b.encode()
        self.assertEqual(to_c, from_a)

        # C recibe y parsea (igual que B o distinto, no importa para el formato).
        at_c = ContainerV1.decode(to_c)
        self.assertEqual([obj.type for obj in at_c.objects], [1, 237, 2, 242])
        self.assertEqual(at_c.encode(), from_a)

    def test_relay_no_known_types(self):
        """B no conoce nada; reenvia byte-for-byte."""
        from_a = hex_vectors.make_unknown_object()

        # B recibe. No conoce ningun tipo.
        at_b = ContainerV1.decode(from_a)
        known_to_b: Set[int] = set()
        self.assertEqual(len([o for o in at_b.objects if o.type in known_to_b]), 0)

        # B reenvia sin tocar VALUE.
        to_c = at_b.encode()
        self.assertEqual(to_c, from_a)

        # C recibe exactamente lo mismo.
        at_c = ContainerV1.decode(to_c)
        self.assertEqual(at_c.encode(), from_a)


class ContainerV1AdversarialTests(unittest.TestCase):
    """Fase 4.7: atacar V1 sin modificarlo."""

    def _valid_container(self) -> bytes:
        return ContainerV1(objects=[
            ObjectV1(type=1, id=0, value=b"abc"),
            ObjectV1(type=2, id=1, value=b"de"),
        ]).encode()

    def test_length_65535_with_few_bytes(self):
        """Objeto anuncia 65535 bytes de value, solo existen 2."""
        # Container: payload de 6 bytes = object header 4 + 2 bytes de value.
        # El objeto dice LENGTH=0xFFFF.
        raw = bytearray(b"\x01\x00\x01\x00\x06\x01\x00\xff\xffXY")
        with self.assertRaises(ContainerError):
            ContainerV1.decode(bytes(raw))

    def test_payload_length_correct_count_impossible(self):
        """PAYLOAD_LENGTH correcto, OBJECT_COUNT imposible."""
        raw = bytearray(b"\x01\x00\xff\x00\x08\x01\x00\x00\x00\x02\x00\x00\x00")
        # 255 objetos anunciados, payload de 8 bytes = dos objetos de 4 bytes (value 0).
        with self.assertRaises(ContainerError):
            ContainerV1.decode(bytes(raw))

    def test_duplicate_id_allowed(self):
        """ID duplicado no es corrupcion estructural."""
        raw = ContainerV1(objects=[
            ObjectV1(type=1, id=7, value=b"a"),
            ObjectV1(type=2, id=7, value=b"b"),
        ]).encode()
        decoded = ContainerV1.decode(raw)
        self.assertEqual([obj.id for obj in decoded.objects], [7, 7])
        self.assertEqual(decoded.encode(), raw)

    def test_container_truncated_at_each_byte(self):
        """Cortar un Container valido byte a byte; todo debe fallar."""
        raw = self._valid_container()
        for cut in range(len(raw)):
            with self.subTest(cut=cut):
                if cut == len(raw):
                    # El original es valido; probamos cortes parciales.
                    continue
                with self.assertRaises(ContainerError):
                    ContainerV1.decode(raw[:cut])

    def test_random_bit_flips(self):
        """Flip de bits nunca causa crash; si decodifica, no es el original."""
        raw = self._valid_container()
        for i in range(len(raw) * 8):
            flipped = bytearray(raw)
            byte_idx = i // 8
            bit_idx = i % 8
            flipped[byte_idx] ^= (1 << bit_idx)
            with self.subTest(i=i):
                try:
                    decoded = ContainerV1.decode(bytes(flipped))
                except ContainerError:
                    continue
                # Si es estructuralmente valido, el contenido difiere del original.
                self.assertNotEqual(decoded.encode(), raw)


class ContainerV1FuzzTests(unittest.TestCase):
    """Fuzz estructural: ninguna entrada aleatoria debe romper el parser."""

    def test_random_containers_roundtrip(self):
        """Generar contenedores aleatorios y verificar round-trip."""
        import random
        random.seed(42)
        for _ in range(200):
            num_objects = random.randint(0, 50)
            objects = []
            for i in range(num_objects):
                obj_type = random.randint(1, 254)
                obj_id = random.randint(0, 254)
                value_len = random.randint(0, 100)
                value = bytes(random.randint(0, 255) for _ in range(value_len))
                objects.append(ObjectV1(type=obj_type, id=obj_id, value=value))
            container = ContainerV1(objects=objects)
            try:
                raw = container.encode()
            except ContainerError:
                # Puede exceder limites V1; saltamos esos casos.
                continue
            decoded = ContainerV1.decode(raw)
            self.assertEqual(decoded.encode(), raw)

    def test_random_bytes_never_crash(self):
        """Bytes aleatorios nunca deben causar crash ni leer fuera de bounds."""
        import random
        random.seed(123)
        for _ in range(500):
            length = random.randint(0, 128)
            data = bytes(random.randint(0, 255) for _ in range(length))
            try:
                ContainerV1.decode(data)
            except ContainerError:
                pass  # Comportamiento esperado.

    def test_random_corruptions_of_valid_containers(self):
        """Corromper contenedores validos aleatoriamente: solo ContainerError."""
        import random
        random.seed(456)

        def _make_random() -> bytes:
            num_objects = random.randint(1, 5)
            objects = [
                ObjectV1(
                    type=random.randint(1, 254),
                    id=random.randint(0, 254),
                    value=bytes(random.randint(0, 255) for _ in range(random.randint(0, 20)))
                )
                for _ in range(num_objects)
            ]
            return ContainerV1(objects=objects).encode()

        for _ in range(300):
            raw = _make_random()
            if len(raw) < 6:
                continue
            # Cortar, flip, o mutar un length.
            corrupted = bytearray(raw)
            op = random.randint(0, 2)
            if op == 0:
                cut = random.randint(0, len(corrupted) - 1)
                corrupted = corrupted[:cut]
            elif op == 1:
                idx = random.randint(0, len(corrupted) - 1)
                corrupted[idx] = random.randint(0, 255)
            else:
                # Agrandar un length en el payload.
                if len(corrupted) > 7:
                    corrupted[7] = 0xFF
                    corrupted[8] = 0xFF
            try:
                ContainerV1.decode(bytes(corrupted))
            except ContainerError:
                pass  # Esperado.


if __name__ == "__main__":
    unittest.main()
