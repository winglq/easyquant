from easyquant.main_engine import MainEngine
from oslo_config import cfg


def main():
    cfg.CONF(args=[],
             project='easyquantd')

    m = MainEngine(broker=None)
    m.load_strategy()
    m.start()


if __name__ == "__main__":
    main()
