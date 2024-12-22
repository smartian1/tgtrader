# encoding: utf-8
from loguru import logger
from tgtrader.strategy_config import StrategyConfig
from tgtrader.streamlit_pages.dao.t_user_strategy import UserStrategy
import json

class UserStrategyService:
    """用户策略服务"""
    
    @classmethod
    def get_user_strategies(cls, user_id: int):
        """获取用户的所有策略"""
        try:
            strategies = UserStrategy.get_user_strategies(user_id)
            return [{
                'id': s.id,
                'strategy': json.loads(s.strategy),
                'create_time': s.create_time,
                'update_time': s.update_time
            } for s in strategies]
        except Exception as e:
            logger.exception(e)
            raise Exception(f"获取用户策略失败: {str(e)}")
    
    @classmethod
    def get_strategy(cls, user_id: int, strategy_id: int) -> UserStrategy:
        """获取用户策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            UserStrategy: 策略对象
        """
        try:
            ret = UserStrategy.get_strategy(user_id, strategy_id)
            return ret
        except UserStrategy.DoesNotExist as e:
            logger.exception(e)
            raise Exception(f"策略不存在: {strategy_id}")
        except Exception as e:
            logger.exception(e)
            raise Exception(f"获取策略失败: {str(e)}")

    @classmethod 
    def create_strategy(cls, user_id: int, strategy_config: StrategyConfig):
        """创建新的策略"""
        try:
            config = strategy_config.to_json()

            # 保存策略
            strategy = UserStrategy.create_strategy(
                user_id=user_id,
                strategy=config
            )
            return {
                'id': strategy.id,
                'strategy': json.loads(strategy.strategy),
                'create_time': strategy.create_time,
                'update_time': strategy.update_time
            }
        except Exception as e:
            logger.exception(e)
            raise Exception(f"创建策略失败: {str(e)}")

    @classmethod
    def update_strategy(cls, user_id: int, strategy_id: int, strategy_config: StrategyConfig):
        """更新策略"""
        try:
            # 验证策略配置格式
            config = strategy_config.to_json()
            
            # 更新策略
            UserStrategy.update_strategy(
                user_id=user_id,
                strategy_id=strategy_id,
                strategy=config
            )
        except Exception as e:
            logger.exception(e)
            raise Exception(f"更新策略失败: {str(e)}")

    @classmethod
    def delete_strategy(cls, user_id: int, strategy_id: int):
        """删除策略"""
        try:
            UserStrategy.delete_strategy(user_id, strategy_id)
        except Exception as e:
            logger.exception(e) 
            raise Exception(f"删除策略失败: {str(e)}")

    @classmethod
    def init_table(cls):
        """初始化数据表"""
        UserStrategy.init_table()
