"""roles.py — Store de roles por identidad (control de acceso por rol).

Fase nueva (interfaz web): el flujo del producto distingue entre usuarios
``user`` (solo turismo) y ``admin`` (turismo + panel de enrolamiento).

DECISIÓN: el rol se guarda en un store DESACOPLADO de la galería
(``data/roles.json``) para NO tocar el formato pickle de la galería
(``{identidad: [embedding, ...]}``). Así la parte de Re-ID de Leandro y la
metadata de roles evolucionan por separado.

Contrato:
    def get_role(identity: str) -> str        # "admin" | "user" (default "user")
    def set_role(identity: str, role: str) -> None
    def load_roles() -> dict
"""

import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# Ruta del store de roles. Mismo directorio que la galería para que el volumen
# persistente del despliegue cubra ambos (ver implementation_plan §7.2).
ROLES_PATH = os.path.join("data", "roles.json")

VALID_ROLES = ("user", "admin")
DEFAULT_ROLE = "user"


def load_roles(path: str = ROLES_PATH) -> Dict[str, str]:
    """Carga el mapa ``{identidad: rol}`` desde disco.

    Devuelve un dict vacío si el archivo no existe todavía (primera ejecución)
    o si está corrupto — nunca lanza, para que el arranque de la API no dependa
    de que el archivo exista.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning(f"{path} no contiene un objeto JSON; se ignora.")
            return {}
        # Normalizar: solo valores válidos
        return {
            str(ident): (role if role in VALID_ROLES else DEFAULT_ROLE)
            for ident, role in data.items()
        }
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"No se pudo leer {path}: {e}. Se asume sin roles.")
        return {}


def get_role(identity: str, path: str = ROLES_PATH) -> str:
    """Devuelve el rol de ``identity`` (``"admin"`` | ``"user"``).

    Identidades sin entrada explícita en ``roles.json`` → ``"user"`` por defecto.
    """
    roles = load_roles(path)
    return roles.get(identity, DEFAULT_ROLE)


def set_role(identity: str, role: str, path: str = ROLES_PATH) -> None:
    """Asigna ``role`` a ``identity`` y persiste el cambio en disco.

    Args:
        identity: nombre de la identidad (mismo key que en la galería).
        role: ``"user"`` o ``"admin"``.

    Raises:
        ValueError: si ``role`` no es uno de los roles válidos.
    """
    if role not in VALID_ROLES:
        raise ValueError(
            f"Rol inválido: '{role}'. Debe ser uno de {VALID_ROLES}."
        )
    roles = load_roles(path)
    roles[identity] = role
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=2)
    logger.info(f"Rol '{role}' asignado a '{identity}' en {path}.")
