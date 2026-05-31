import time
import logging
import os
import requests
import anthropic
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
    from notifier import notify_error
    last_run_date = ""
    logging.info("Scheduler LinkedIn iniciado. Publicará a las 10:30 cada día.")

    while True:
        now = datetime.now()
        if should_run(last_run_date):
            logging.info("Ejecutando publicación LinkedIn...")
            last_run_date = str(now.date())  # marcar antes para evitar doble ejecución
            try:
                run()
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 401:
                    logging.error("LinkedIn token caducado (401)")
                    notify_error("linkedin_token")
                else:
                    logging.error(f"HTTP error: {e}")
                    notify_error("generic", str(e))
            except anthropic.BadRequestError as e:
                if "credit balance" in str(e):
                    logging.error("Anthropic sin créditos (400)")
                    notify_error("anthropic_credits")
                else:
                    logging.error(f"Anthropic error: {e}")
                    notify_error("generic", str(e))
            except Exception as e:
                logging.error(f"Error en publicación: {e}")
                notify_error("generic", str(e))
        time.sleep(30)

if __name__ == "__main__":
    main()
