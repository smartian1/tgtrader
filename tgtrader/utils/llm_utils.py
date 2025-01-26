# encoding: utf-8

from typing import Dict, Callable
from dataclasses import dataclass
import pandas as pd
import re
import os
from openai import OpenAI
import json
from tgtrader.dao.t_api_key import TApiKey

def _replace_template_vars(template: str, row: pd.Series) -> str:
    """替换模板中被{{}}包裹的变量为行数据中的值。
    
    Args:
        template: 包含{{}}变量的模板字符串
        row: 包含替换变量值的Pandas Series
        
    Returns:
        str: 替换变量后的模板字符串
    """
    # 找到所有{{}}中的变量
    vars = re.findall(r'\{\{(.*?)\}\}', template)
    result = template
    
    # 替换每个变量
    for var in vars:
        var = var.strip()
        if var in row:
            result = result.replace('{{' + var + '}}', str(row[var]))
            
    return result

def openai_client(base_url: str, model: str, api_key: str, prompt_template: str, input_data: Dict[str, pd.DataFrame], callback: Callable):
    """通过OpenAI API处理数据并替换模板。
    
    Args:
        base_url: API基础URL
        model: 要使用的模型名称
        api_key: OpenAI API密钥
        prompt_template: 带有{{}}变量的模板字符串
        input_data: 要处理的数据帧字典
        callback: 处理日志的回调函数，接收message和message_type两个参数
    """
    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    callback("开始处理数据...", "info")
    
    results = []
    for df_name, df in input_data.items():
        for index, row in df.iterrows():
            # 处理模板变量替换
            processed_prompt = _replace_template_vars(prompt_template, row)
            
            try:
                # 调用API
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a financial news analyst. You must respond with ONLY a valid JSON object. Do not include any other text, markdown formatting, or code block markers. The response should be directly parseable by JSON.parse()."},
                        {"role": "user", "content": processed_prompt}
                    ]
                )
                
                # 解析返回的JSON结果
                response_text = completion.choices[0].message.content
                callback(f"处理第{index}行, 模型返回结果: {response_text}", "info")
                
                # 直接解析JSON响应
                response_json = json.loads(response_text)
                
                # 合并原始行数据和模型返回结果
                merged_result = {**row.to_dict(), **response_json}
                results.append(merged_result)
                
            except Exception as e:
                error_msg = f"处理行 {index} 时发生错误: {str(e)}"
                callback(error_msg, "error")
                continue
    
    return pd.DataFrame(results)

@dataclass
class LLMUtils:
    model_id: int
    api_key: str
    prompt_template: str

    model_func_config_dict = {
        "qwen-plus-latest": {
            "func": openai_client,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "qwen-turbo-latest": {
            "func": openai_client,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
    }

    def __get_model_config(self):
        model_config = TApiKey.get_model_config(self.model_id)
        return model_config

    def run(self, input_data: Dict[str, pd.DataFrame], callback: Callable) -> pd.DataFrame:
        """运行指定模型的处理函数。
        
        Args:
            input_data: 输入数据帧字典
            callback: 回调函数
        
        Returns:
            pd.DataFrame: 处理后的数据帧
        
        Raises:
            ValueError: 如果模型不存在
        """
        model_config = self.__get_model_config()
        if not model_config:
            raise ValueError(f"模型{self.model_id}不存在")
        
        model_func_config = self.model_func_config_dict.get(model_config.api_key_name)
        if not model_func_config:
            raise ValueError(f"模型{model_config.api_key_name}不存在")
        
        func = model_func_config.get("func")
        if not func:
            raise ValueError(f"模型{model_config.model_name}的处理函数不存在")
        
        return func(model_func_config.get("base_url"), model_config.model_name, model_config.api_key, self.prompt_template, input_data, callback)
