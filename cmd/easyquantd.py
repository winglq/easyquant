from easyquant.main_engine import MainEngine


def main():
    m = MainEngine(broker=None)
    m.load_strategy()
    m.start()


if __name__ == "__main__":
    main()
