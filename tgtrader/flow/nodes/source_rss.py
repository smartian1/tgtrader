# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from typing import Callable
from tgtrader.common import DataSource
from tgtrader.utils.duckdb_query import DuckDBQuery
from dataclasses import dataclass
import feedparser
import pandas as pd

@dataclass
class RSSSource:
    id: int
    url: str

    def extract_data(self) -> pd.DataFrame:
        """从RSS源提取数据.

        Returns:
            pd.DataFrame: 包含title, description, pubDate, guid的数据框
        """
        # 解析RSS feed
        feed = feedparser.parse(self.url)
        
        # 提取所需字段
        data = []
        for entry in feed.entries:
            item = {
                'title': entry.get('title', ''),
                'desc': entry.get('description', ''),
                'guid': entry.get('guid', entry.get('id', '')),  # 有些RSS用id代替guid
                'pub_time': pd.to_datetime(entry.get('published', '')).timestamp()  # 转换为时间戳
            }
            data.append(item)
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        return df

class SourceRSSNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        """
        config样例:
        {"type": "data_source_rss", "content": {"selected_rss_ids": [2], "rss_info": [{"id": 2, "url": "https://www.baidu.com/rss"}]}}
        """
        if process_callback:
            process_callback(f"【节点: {self.node_label}】开始执行RSS源数据提取", message_type="info")

        try:
            content = self.config["content"]
            if not content:
                raise ValueError("content is required")
            
            selected_rss = content.get("rss_info", dict())
            if not selected_rss:
                raise ValueError("rss_info is required")
            
            ret_data_df = []
            for rss_info in selected_rss:
                rss_source = RSSSource(rss_info["id"], rss_info["url"])
                df = rss_source.extract_data()
                if df is not None and not df.empty:
                    ret_data_df.append(df)
            
            df = pd.concat(ret_data_df)
            # 根据guid去重
            df = df.drop_duplicates(subset=['guid'])
                
        except Exception as e:
            if process_callback:
                process_callback(f"【节点: {self.node_label}】, 查询失败: {e}", message_type="error")
            raise e

        if process_callback:
            process_callback(f"【节点: {self.node_label}】, 查询结果数量: {len(df)}", message_type="info")

        return df
