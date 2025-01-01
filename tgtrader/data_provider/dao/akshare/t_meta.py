# encoding: utf-8
from tgtrader.common import DataSource
from tgtrader.data_provider.dao.akshare.common import main_db
from tgtrader.data_provider.dao.models.t_meta_model import T_Meta_Model
from tgtrader.data_provider.dao.models.common import register_model


@register_model(DataSource.Akshare, 't_meta')
class T_Meta(T_Meta_Model):
    
    @classmethod
    def init_table(cls):
        # 初始化表
        with main_db:
            table_exists = T_Meta.table_exists()
            if not table_exists:
                main_db.create_tables([T_Meta])  # 如果表不存在，创建表
