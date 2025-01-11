# encoding: utf-8

from tgtrader.streamlit_pages.dao.t_flow import FlowCfg


class FlowConfigService:
    def __init__(self):
        pass

    def generate_new_flow(self) -> FlowCfg:
        pass

    def get_flow_for_edit(self, flow_id):
        pass

    def save_node_config(self, node_id,node_config, flow_id):
        pass

    def save_flow(self, user_id, flow_id):
        pass
    