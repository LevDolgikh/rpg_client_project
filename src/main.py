# Application start file
from game import RPG_client
from ui import RPG_ui


def main():

    # Init
    rpg_client = RPG_client()
    app = RPG_ui(rpg_client)

    app.mainloop()


if __name__ == "__main__":
    main()