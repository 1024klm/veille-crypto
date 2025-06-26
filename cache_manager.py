import os
import json
import redis
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import logging
from functools import wraps
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        """Initialise le gestionnaire de cache."""
        load_dotenv()
        
        # Configuration Redis
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
        # Tentative de connexion à Redis
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=False
            )
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Connexion Redis établie")
        except (redis.ConnectionError, redis.TimeoutError):
            self.redis_available = False
            logger.warning("Redis non disponible, utilisation du cache en mémoire")
            self.memory_cache = {}
            
        # Configuration des TTL par type de données
        self.ttl_config = {
            'market_prices': 60,  # 1 minute
            'twitter_tweets': 300,  # 5 minutes
            'rss_feeds': 600,  # 10 minutes
            'sentiment_analysis': 1800,  # 30 minutes
            'whale_alerts': 120,  # 2 minutes
            'trending_coins': 300,  # 5 minutes
            'google_trends': 3600,  # 1 heure
            'technical_analysis': 900,  # 15 minutes
            'default': 300  # 5 minutes par défaut
        }
        
        # Statistiques de cache
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'evictions': 0
        }
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Génère une clé de cache unique."""
        return f"crypto_veille:{prefix}:{identifier}"
    
    def _serialize(self, data: Any) -> bytes:
        """Sérialise les données pour le stockage."""
        return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Désérialise les données depuis le stockage."""
        return pickle.loads(data)
    
    def get(self, key: str, prefix: str = 'general') -> Optional[Any]:
        """Récupère une valeur du cache."""
        full_key = self._generate_key(prefix, key)
        
        try:
            if self.redis_available:
                data = self.redis_client.get(full_key)
                if data:
                    self.stats['hits'] += 1
                    return self._deserialize(data)
            else:
                # Cache en mémoire
                if full_key in self.memory_cache:
                    data, expiry = self.memory_cache[full_key]
                    if datetime.now() < expiry:
                        self.stats['hits'] += 1
                        return data
                    else:
                        # Donnée expirée
                        del self.memory_cache[full_key]
                        self.stats['evictions'] += 1
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
            self.stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, prefix: str = 'general', ttl: Optional[int] = None) -> bool:
        """Stocke une valeur dans le cache."""
        full_key = self._generate_key(prefix, key)
        
        # Détermination du TTL
        if ttl is None:
            ttl = self.ttl_config.get(prefix, self.ttl_config['default'])
        
        try:
            if self.redis_available:
                serialized_data = self._serialize(value)
                self.redis_client.setex(full_key, ttl, serialized_data)
            else:
                # Cache en mémoire avec expiration
                expiry = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[full_key] = (value, expiry)
                
                # Nettoyage périodique du cache mémoire
                self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage dans le cache: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def delete(self, key: str, prefix: str = 'general') -> bool:
        """Supprime une valeur du cache."""
        full_key = self._generate_key(prefix, key)
        
        try:
            if self.redis_available:
                return bool(self.redis_client.delete(full_key))
            else:
                if full_key in self.memory_cache:
                    del self.memory_cache[full_key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Supprime toutes les clés avec un préfixe donné."""
        pattern = self._generate_key(prefix, '*')
        count = 0
        
        try:
            if self.redis_available:
                # Utilisation de SCAN pour éviter le blocage
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        count += len(keys)
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Cache mémoire
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"crypto_veille:{prefix}:")]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache: {str(e)}")
            return 0
    
    def _cleanup_memory_cache(self):
        """Nettoie les entrées expirées du cache mémoire."""
        if not self.redis_available and len(self.memory_cache) > 1000:
            current_time = datetime.now()
            expired_keys = []
            
            for key, (_, expiry) in self.memory_cache.items():
                if current_time >= expiry:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'total_requests': total_requests,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'errors': self.stats['errors'],
            'evictions': self.stats['evictions'],
            'redis_available': self.redis_available
        }
        
        if self.redis_available:
            try:
                info = self.redis_client.info()
                stats['redis_memory_used'] = info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = self.redis_client.dbsize()
            except:
                pass
        else:
            stats['memory_cache_size'] = len(self.memory_cache)
        
        return stats
    
    def cache_result(self, prefix: str = 'general', ttl: Optional[int] = None):
        """Décorateur pour mettre en cache les résultats de fonction."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Génération de la clé basée sur la fonction et ses arguments
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
                
                # Tentative de récupération depuis le cache
                cached_value = self.get(cache_key_hash, prefix)
                if cached_value is not None:
                    logger.debug(f"Cache hit pour {func.__name__}")
                    return cached_value
                
                # Exécution de la fonction
                result = func(*args, **kwargs)
                
                # Stockage du résultat
                self.set(cache_key_hash, result, prefix, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def batch_get(self, keys: List[str], prefix: str = 'general') -> Dict[str, Any]:
        """Récupère plusieurs valeurs du cache en une fois."""
        results = {}
        
        if self.redis_available:
            try:
                full_keys = [self._generate_key(prefix, key) for key in keys]
                values = self.redis_client.mget(full_keys)
                
                for key, value in zip(keys, values):
                    if value:
                        results[key] = self._deserialize(value)
                        self.stats['hits'] += 1
                    else:
                        results[key] = None
                        self.stats['misses'] += 1
                        
            except Exception as e:
                logger.error(f"Erreur lors de la récupération batch: {str(e)}")
                self.stats['errors'] += 1
        else:
            # Cache mémoire
            for key in keys:
                results[key] = self.get(key, prefix)
        
        return results
    
    def batch_set(self, data: Dict[str, Any], prefix: str = 'general', ttl: Optional[int] = None) -> bool:
        """Stocke plusieurs valeurs dans le cache en une fois."""
        if ttl is None:
            ttl = self.ttl_config.get(prefix, self.ttl_config['default'])
        
        success = True
        
        if self.redis_available:
            try:
                pipe = self.redis_client.pipeline()
                
                for key, value in data.items():
                    full_key = self._generate_key(prefix, key)
                    serialized_data = self._serialize(value)
                    pipe.setex(full_key, ttl, serialized_data)
                
                pipe.execute()
                
            except Exception as e:
                logger.error(f"Erreur lors du stockage batch: {str(e)}")
                success = False
        else:
            # Cache mémoire
            for key, value in data.items():
                if not self.set(key, value, prefix, ttl):
                    success = False
        
        return success

# Instance globale du gestionnaire de cache
cache_manager = CacheManager()

# Exemple d'utilisation avec décorateur
@cache_manager.cache_result(prefix='market_prices', ttl=60)
def get_expensive_market_data(symbol: str) -> Dict[str, Any]:
    """Exemple de fonction coûteuse qui bénéficie du cache."""
    # Simulation d'une opération coûteuse
    import time
    time.sleep(2)
    return {'symbol': symbol, 'price': 50000, 'timestamp': datetime.now().isoformat()}