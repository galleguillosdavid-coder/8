"""
Escenarios de Identity para la prueba de fuego de Fase 5.2
(ver docs/IDENTITY_FIRE_TEST.md).

Estos escenarios reutilizan ContainerV1/ObjectV1 (Fase 4.6/4.7)
SIN MODIFICARLOS. El objetivo es demostrar experimentalmente que
Identity, Evidence, Rotation, Revocation y Delegation pueden
representarse enteramente como Objects genericos, sin requerir ningun
campo nuevo en Packet, Container u Object Header.

Los valores de TYPE usados aqui son ilustrativos (namespace de
ejemplo). El Core nunca les asigna significado.
"""

from .container_v1 import ContainerV1, ObjectV1

# TYPEs ilustrativos para el Profile de ejemplo "identity.v1".
# El Core no conoce estos numeros; son solo para el experimento.
TYPE_CONTACT = 1
TYPE_IDENTITY_DECLARED = 20
TYPE_IDENTITY_KNOWLEDGE = 21
TYPE_EVIDENCE = 22
TYPE_IDENTITY_ROTATION = 23
TYPE_IDENTITY_REVOCATION = 24
TYPE_IDENTITY_DELEGATION = 25


def case_a_identity_presented() -> bytes:
    """A: Identity presentada por primera vez."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-pubkey"),
    ]).encode()


def case_b_unknown_identity_type() -> bytes:
    """B: Identity de un Profile futuro, TYPE desconocido para el receptor."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_CONTACT, id=1, value=b"contact"),
        ObjectV1(type=0xE1, id=2, value=b"identity-from-the-future"),
    ]).encode()


def case_c_identity_observed_not_verified() -> bytes:
    """C: Identity observada, no verificada. Value interno definido por Profile."""
    return ContainerV1(objects=[
        ObjectV1(
            type=TYPE_IDENTITY_KNOWLEDGE, id=1,
            value=b"identity:X;truth:observed;source:A;confidence:medium"
        ),
    ]).encode()


def case_d_identity_verified_with_evidence() -> bytes:
    """D: Identity + Evidence (referencia local, opaca para el Core)."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-pubkey"),
        ObjectV1(type=TYPE_EVIDENCE, id=2, value=b"ref:01;challenge-response-ok"),
    ]).encode()


def case_e_two_identities_same_node() -> bytes:
    """E: dos identidades en el mismo nodo, mismo Container."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-sensor"),
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=2, value=b"X-control"),
    ]).encode()


def case_g_rotation() -> bytes:
    """G: rotacion de identidad, referencia a la nueva clave."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"Key-B-new"),
        ObjectV1(type=TYPE_IDENTITY_ROTATION, id=2, value=b"sig(KeyA over KeyB);ref:01"),
    ]).encode()


def case_h_revocation() -> bytes:
    """H: revocacion referenciando un ID local."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-pubkey"),
        ObjectV1(type=TYPE_IDENTITY_REVOCATION, id=2, value=b"ref:01;revoked-at:t;reason:opaque"),
    ]).encode()


def case_i_delegation() -> bytes:
    """I: A delega en B con un scope opaco para el Core."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"A"),
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=2, value=b"B"),
        ObjectV1(type=TYPE_IDENTITY_DELEGATION, id=3, value=b"from:01;to:02;scope:telemetry"),
    ]).encode()


def case_j_anonymous_contact() -> bytes:
    """J: Container sin ningun Object de identidad."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_CONTACT, id=1, value=b"anonymous-contact"),
    ]).encode()


def case_n_replay_pair() -> tuple:
    """
    N: dos "envios" con bytes identicos (replay). Se devuelve el mismo
    payload dos veces para demostrar que el Core no puede, por diseno,
    distinguirlos.
    """
    original = ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-pubkey"),
    ]).encode()
    replay = bytes(original)  # bytes identicos, "capturados" y reenviados
    return original, replay


def case_o_binding_conflict() -> bytes:
    """O: evidencia y revocacion contradictorias sobre el mismo ref."""
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=1, value=b"X-pubkey"),
        ObjectV1(type=TYPE_EVIDENCE, id=2, value=b"ref:01;says:verified"),
        ObjectV1(type=TYPE_IDENTITY_REVOCATION, id=3, value=b"ref:01;says:revoked"),
    ]).encode()


def case_p_duplicate_id() -> bytes:
    """
    P: caso critico. Dos Objects de identidad comparten el mismo ID.
    Una Evidence referencia ese ID, quedando ambigua a nivel de Profile.
    """
    return ContainerV1(objects=[
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=7, value=b"X"),
        ObjectV1(type=TYPE_IDENTITY_DECLARED, id=7, value=b"Y"),
        ObjectV1(type=TYPE_EVIDENCE, id=9, value=b"ref:07;says:verified"),
    ]).encode()


# Escenarios usados para el test de round-trip generico.
ALL_SCENARIOS = [
    ("A_identity_presented", case_a_identity_presented),
    ("B_unknown_identity_type", case_b_unknown_identity_type),
    ("C_observed_not_verified", case_c_identity_observed_not_verified),
    ("D_verified_with_evidence", case_d_identity_verified_with_evidence),
    ("E_two_identities_same_node", case_e_two_identities_same_node),
    ("G_rotation", case_g_rotation),
    ("H_revocation", case_h_revocation),
    ("I_delegation", case_i_delegation),
    ("J_anonymous_contact", case_j_anonymous_contact),
    ("O_binding_conflict", case_o_binding_conflict),
    ("P_duplicate_id", case_p_duplicate_id),
]
