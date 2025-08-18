from game_bot import GameBot
from datetime import datetime
import logging

if __name__ == "__main__":
    logging.basicConfig(
        filename=f"logs/{datetime.now().strftime("%d.%m.%y_%H-%M-%S")}.log",
        level=logging.INFO
    )
    bot = GameBot()
