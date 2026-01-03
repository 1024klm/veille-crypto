#!/usr/bin/env python3
"""
Scheduler pour exécution automatique du bot de veille crypto.
Permet de planifier des tâches récurrentes sans dépendance externe (cron, systemd, etc.)
"""

import os
import sys
import time
import signal
import logging
import argparse
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass
from queue import Queue, Empty
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Représente une tâche planifiée."""
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True


class CryptoScheduler:
    """Scheduler pour les tâches de veille crypto."""

    def __init__(self):
        """Initialise le scheduler."""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.stop_event = threading.Event()
        self.stats = {
            'start_time': None,
            'total_runs': 0,
            'total_errors': 0
        }

        # Gestion des signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Gère les signaux d'arrêt."""
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        self.stop()

    def add_task(self, name: str, func: Callable, interval_minutes: int, enabled: bool = True):
        """Ajoute une tâche planifiée."""
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_minutes * 60,
            next_run=datetime.now(),
            enabled=enabled
        )
        self.tasks[name] = task
        logger.info(f"Tâche ajoutée: {name} (toutes les {interval_minutes} min)")

    def remove_task(self, name: str):
        """Supprime une tâche."""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Tâche supprimée: {name}")

    def enable_task(self, name: str):
        """Active une tâche."""
        if name in self.tasks:
            self.tasks[name].enabled = True
            logger.info(f"Tâche activée: {name}")

    def disable_task(self, name: str):
        """Désactive une tâche."""
        if name in self.tasks:
            self.tasks[name].enabled = False
            logger.info(f"Tâche désactivée: {name}")

    def _run_task(self, task: ScheduledTask):
        """Exécute une tâche."""
        try:
            logger.info(f"Exécution de la tâche: {task.name}")
            start_time = time.time()

            task.func()

            elapsed = time.time() - start_time
            task.run_count += 1
            task.last_run = datetime.now()
            task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
            self.stats['total_runs'] += 1

            logger.info(f"Tâche {task.name} terminée en {elapsed:.2f}s")

        except Exception as e:
            task.error_count += 1
            self.stats['total_errors'] += 1
            logger.error(f"Erreur dans la tâche {task.name}: {str(e)}")

            # Reprogrammer même en cas d'erreur
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

    def run(self):
        """Lance le scheduler."""
        self.running = True
        self.stats['start_time'] = datetime.now()

        logger.info("=" * 60)
        logger.info("Démarrage du Crypto Scheduler")
        logger.info(f"Tâches planifiées: {len(self.tasks)}")
        for name, task in self.tasks.items():
            logger.info(f"  - {name}: toutes les {task.interval_seconds // 60} min")
        logger.info("=" * 60)

        try:
            while self.running and not self.stop_event.is_set():
                now = datetime.now()

                for task in self.tasks.values():
                    if not task.enabled:
                        continue

                    if task.next_run and now >= task.next_run:
                        # Exécution dans un thread séparé pour ne pas bloquer
                        thread = threading.Thread(
                            target=self._run_task,
                            args=(task,),
                            name=f"Task-{task.name}"
                        )
                        thread.start()

                # Attente avant la prochaine vérification
                self.stop_event.wait(timeout=10)

        except KeyboardInterrupt:
            logger.info("Interruption clavier détectée")
        finally:
            self.stop()

    def stop(self):
        """Arrête le scheduler."""
        self.running = False
        self.stop_event.set()
        logger.info("Scheduler arrêté")
        self._save_stats()

    def _save_stats(self):
        """Sauvegarde les statistiques."""
        try:
            stats = {
                'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
                'stop_time': datetime.now().isoformat(),
                'total_runs': self.stats['total_runs'],
                'total_errors': self.stats['total_errors'],
                'tasks': {}
            }

            for name, task in self.tasks.items():
                stats['tasks'][name] = {
                    'run_count': task.run_count,
                    'error_count': task.error_count,
                    'last_run': task.last_run.isoformat() if task.last_run else None
                }

            os.makedirs('data', exist_ok=True)
            with open('data/scheduler_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)

        except Exception as e:
            logger.error(f"Erreur sauvegarde stats: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du scheduler."""
        return {
            'running': self.running,
            'uptime': str(datetime.now() - self.stats['start_time']) if self.stats['start_time'] else None,
            'total_runs': self.stats['total_runs'],
            'total_errors': self.stats['total_errors'],
            'tasks': {
                name: {
                    'enabled': task.enabled,
                    'run_count': task.run_count,
                    'error_count': task.error_count,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                }
                for name, task in self.tasks.items()
            }
        }


def run_main_veille():
    """Exécute la veille principale."""
    from main import main
    import sys

    # Sauvegarde des arguments originaux
    original_argv = sys.argv.copy()

    try:
        sys.argv = ['main.py', '--free-only', '--skip-twitter']
        main()
    finally:
        sys.argv = original_argv


def run_technical_analysis():
    """Exécute l'analyse technique des principales cryptos."""
    from technical_analyzer import TechnicalAnalyzer

    analyzer = TechnicalAnalyzer()
    coins = ['bitcoin', 'ethereum', 'solana']

    for coin in coins:
        try:
            analysis = analyzer.analyze_coin(coin, days=7)
            if 'error' not in analysis:
                logger.info(f"Analyse technique {coin}: Signal={analysis['signals']['action']}")
        except Exception as e:
            logger.error(f"Erreur analyse {coin}: {str(e)}")


def run_anomaly_detection():
    """Exécute la détection d'anomalies."""
    from anomaly_detector import AnomalyDetector
    from market_data_fetcher import MarketDataFetcher

    try:
        fetcher = MarketDataFetcher()
        detector = AnomalyDetector()

        market_data = fetcher.fetch_all_market_data()
        anomalies = detector.detect_all_anomalies(market_data)

        if anomalies.get('alerts'):
            logger.warning(f"Anomalies détectées: {len(anomalies['alerts'])}")
            for alert in anomalies['alerts'][:3]:
                logger.warning(f"  - {alert.get('type', 'unknown')}: {alert.get('message', 'N/A')}")

    except Exception as e:
        logger.error(f"Erreur détection anomalies: {str(e)}")


def run_send_daily_summary():
    """Envoie un résumé quotidien."""
    from notifier import CryptoNotifier

    try:
        notifier = CryptoNotifier()

        # Chargement des données
        with open('data/all_data.json', 'r') as f:
            all_data = json.load(f)

        notifier.check_and_notify(all_data)

    except Exception as e:
        logger.error(f"Erreur envoi résumé: {str(e)}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description='Crypto Veille Scheduler')
    parser.add_argument('--veille-interval', type=int, default=15,
                        help='Intervalle de veille en minutes (défaut: 15)')
    parser.add_argument('--analysis-interval', type=int, default=60,
                        help='Intervalle d\'analyse technique en minutes (défaut: 60)')
    parser.add_argument('--anomaly-interval', type=int, default=5,
                        help='Intervalle de détection d\'anomalies en minutes (défaut: 5)')
    parser.add_argument('--summary-interval', type=int, default=360,
                        help='Intervalle de résumé en minutes (défaut: 360 = 6h)')
    parser.add_argument('--disable-veille', action='store_true',
                        help='Désactiver la veille principale')
    parser.add_argument('--disable-analysis', action='store_true',
                        help='Désactiver l\'analyse technique')
    parser.add_argument('--disable-anomaly', action='store_true',
                        help='Désactiver la détection d\'anomalies')
    parser.add_argument('--run-once', action='store_true',
                        help='Exécuter une seule fois et quitter')

    args = parser.parse_args()

    # Création du répertoire data
    os.makedirs('data', exist_ok=True)

    scheduler = CryptoScheduler()

    # Ajout des tâches
    scheduler.add_task(
        name='veille_principale',
        func=run_main_veille,
        interval_minutes=args.veille_interval,
        enabled=not args.disable_veille
    )

    scheduler.add_task(
        name='analyse_technique',
        func=run_technical_analysis,
        interval_minutes=args.analysis_interval,
        enabled=not args.disable_analysis
    )

    scheduler.add_task(
        name='detection_anomalies',
        func=run_anomaly_detection,
        interval_minutes=args.anomaly_interval,
        enabled=not args.disable_anomaly
    )

    scheduler.add_task(
        name='resume_quotidien',
        func=run_send_daily_summary,
        interval_minutes=args.summary_interval,
        enabled=True
    )

    if args.run_once:
        # Exécution unique de toutes les tâches
        logger.info("Mode run-once: exécution de toutes les tâches...")
        for task in scheduler.tasks.values():
            if task.enabled:
                scheduler._run_task(task)
        logger.info("Exécution terminée")
    else:
        # Mode scheduler continu
        print("""
╔══════════════════════════════════════════════════════════════╗
║              CRYPTO VEILLE SCHEDULER                         ║
╠══════════════════════════════════════════════════════════════╣
║  Tâches planifiées:                                          ║
║    - Veille principale: toutes les {} min                   ║
║    - Analyse technique: toutes les {} min                   ║
║    - Détection anomalies: toutes les {} min                  ║
║    - Résumé quotidien: toutes les {} min                   ║
║                                                              ║
║  Appuyez sur Ctrl+C pour arrêter                            ║
╚══════════════════════════════════════════════════════════════╝
        """.format(
            args.veille_interval,
            args.analysis_interval,
            args.anomaly_interval,
            args.summary_interval
        ))

        scheduler.run()


if __name__ == '__main__':
    main()
