# encoding: utf-8

from tgtrader.streamlit_pages.pages.component.data_process import build_flow_page, FlowType


def run():
    build_flow_page(FlowType.AI_FLOW)
