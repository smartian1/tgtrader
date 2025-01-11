# encoding: utf-8
from tgtrader.streamlit_pages.pages.component.data_process import build_flow_page

def run():
    support_node_type_list = ["data_source_db", "processor_python_code", "processor_sql", "sink_db"]
    build_flow_page(support_node_type_list)
