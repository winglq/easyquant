# coding:utf-8
import sys
import traceback


class StrategyTemplate:
    name = 'DefaultStrategyTemplate'

    def __init__(self, user, log_handler, main_engine):
        self.user = user
        self.main_engine = main_engine
        self.clock_engine = main_engine.clock_engine
        # 优先使用自定义 log 句柄, 否则使用主引擎日志句柄
        self.log = self.log_handler() or log_handler
        self.init()
        self._initing = False
        self._inited = False

    def run_before_strategy(self):
        """ If init needs a long time to completed, it will pend loading of
        other strategy. You should put the this kind of init process in this
        function. This function will run before the strategy function of this
        class.
        """
        pass

    def init(self):
        # 进行相关的初始化操作
        pass

    def reload(self):
        self.init()
        self._initing = False
        self._inited = False

    def strategy_wrapper(self, event):
        if self._initing and not self._inited:
            return
        if not self._initing and not self._inited:
            self._initing = True
            self.run_before_strategy()
            self._initing = False
            self._inited = True

        self.strategy(event)

    def strategy(self, event):
        pass

    def run(self, event):
        try:
            self.strategy_wrapper(event)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.log.error(repr(traceback.format_exception(exc_type,
                                                           exc_value,
                                                           exc_traceback)))

    def clock(self, event):
        pass

    def log_handler(self):
        """
        优先使用在此自定义 log 句柄, 否则返回None, 并使用主引擎日志句柄
        :return: log_handler or None
        """
        return None

    def shutdown(self):
        """
        关闭进程前调用该函数
        :return:
        """
        pass
