"""Application entry point."""

import logging

from game import RPGClient
from ui import RPGUI


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    configure_logging()
    rpg_client = RPGClient()
    app = RPGUI(rpg_client)
    app.mainloop()


if __name__ == "__main__":
    main()
