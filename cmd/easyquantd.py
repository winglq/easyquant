from easyquant.main_engine import MainEngine
from oslo_config import cfg
from easyquant.push_engine.quotation_engine import TradeTimeQuotationEngine


def main():
    cfg.CONF(args=[],
             project='easyquantd')

    #m = MainEngine(broker=None, quotation_engines=TradeTimeQuotationEngine)
    m = MainEngine(broker=None)
    m.load_strategy()
    m.start()


if __name__ == "__main__":
    main()
