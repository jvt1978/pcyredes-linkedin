import time
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

PUBLISH_HOUR = 10
PUBLISH_MINUTE = 30

def should_run(last_run_date: str) -> bool:
    now = datetime.now()
    today = str(now.date())
    return (
        today != last_run_date
        and now.hour == PUBLISH_HOUR
        and now.minute == PUBLISH_MINUTE
    )

def main():
    from main import run
    last_run_date = ""
    logging.info("Scheduler LinkedIn iniciado. Publicará a las 10:30 cada día.")

    while True:
        now = datetime.now()
        if should_run(last_run_date):
            logging.info("Ejecutando publicación LinkedIn...")
            try:
                run()
                last_run_date = str(now.date())
            except Exception as e:
                logging.error(f"Error en publicación: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()
