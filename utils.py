import os
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def require_api_key(key_name: str) -> Callable:
    """
    Décorateur pour vérifier la présence d'une clé API.
    
    Args:
        key_name: Nom de la variable d'environnement contenant la clé API
        
    Returns:
        Callable: Le décorateur
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not os.getenv(key_name):
                logger.warning(f"Clé API {key_name} non configurée, on skip.")
                return [] if func.__annotations__.get('return') == list else {}
            return func(*args, **kwargs)
        return wrapper
    return decorator 