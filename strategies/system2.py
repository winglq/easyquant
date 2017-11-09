from strategies.system1 import Strategy as Sys1Strategy
from oslo_config import cfg

turtle_sys2_opts = [
    cfg.StrOpt('sys2_post_url',
               help='Post result to this url'),
]

CONF = cfg.CONF
CONF.register_opts(turtle_sys2_opts)


class Strategy(Sys1Strategy):
    name = 'turtle system2'

    def __init__(self, user, log_handler, main_engine):
        super(Strategy, self).__init__(user, log_handler, main_engine)
        self.days = 60
        self.post_url = CONF.sys2_post_url
