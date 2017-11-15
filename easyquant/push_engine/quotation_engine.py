# coding: utf-8

import easyquotation

from .base_engine import BaseEngine
from easyquant.easydealutils import time as etime
from datetime import datetime
from easyquant.event_engine import Event


class DefaultQuotationEngine(BaseEngine):
    """新浪行情推送引擎"""
    EventType = 'quotation'

    def init(self):
        self.source = easyquotation.use('sina')

    def fetch_quotation(self):
        return self.source.all


class TradeTimeQuotationEngine(BaseEngine):
    def init(self):
        self.source = easyquotation.use('sina')

    def fetch_quotation(self):
        return self.source.all

    def push_quotation(self):
        while self.is_active:

            if not etime.is_tradetime(datetime.now()):
                self.wait()
                continue

            try:
                response_data = self.fetch_quotation()
            except:
                self.wait()
                continue
            event = Event(event_type=self.EventType, data=response_data)
            self.event_engine.put(event)
            self.wait()
