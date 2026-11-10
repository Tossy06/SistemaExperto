"""Hash de contraseñas con scrypt (RNF-04): en la base nunca se guarda la contraseña en texto plano."""
import hashlib
import hmac
import os

_N, _R, _P = 2 ** 14, 8, 1        # parámetros de costo de scrypt


def generar_hash(contrasena: str) -> str:
    """Devuelve «scrypt$n$r$p$sal$huella», listo para guardar en la columna contrasena_hash."""
    sal = os.urandom(16)
    huella = hashlib.scrypt(contrasena.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P)
    return f"scrypt${_N}${_R}${_P}${sal.hex()}${huella.hex()}"


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    """Recalcula la huella con la sal guardada y la compara en tiempo constante."""
    try:
        _, n, r, p, sal, huella = hash_guardado.split("$")
        calculada = hashlib.scrypt(contrasena.encode("utf-8"), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(calculada.hex(), huella)
    except ValueError:
        return False
