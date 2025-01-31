# encoding: utf-8
from datetime import datetime
from typing import List, Tuple, Optional
from peewee import AutoField, TextField, IntegerField, BigIntegerField
from tgtrader.dao.common import BaseModel, db


class TTask(BaseModel):
    """
    任务表模型.
    
    Attributes:
        id (AutoField): 主键自增id
        username (TextField): 用户名
        flow_type (IntegerField): 流程类型
        flow_name (TextField): 流程名称
        flow_id (TextField): 流程ID
        status (IntegerField): 任务状态 0-停止 1-运行中
        crontab (TextField): crontab配置
        create_time (BigIntegerField): 创建时间
        update_time (BigIntegerField): 更新时间
    """
    
    id = AutoField()
    username = TextField(verbose_name='用户名')
    flow_type = IntegerField(verbose_name='流程类型')
    flow_name = TextField(verbose_name='流程名称')
    flow_id = TextField(verbose_name='流程ID')
    status = IntegerField(verbose_name='任务状态', default=0)  # 0-停止 1-运行中
    crontab = TextField(verbose_name='定时配置', default='0 0 * * *')  # 默认每天0点执行
    create_time = BigIntegerField(verbose_name='创建时间', default=lambda: int(datetime.now().timestamp() * 1000))
    update_time = BigIntegerField(verbose_name='更新时间', default=lambda: int(datetime.now().timestamp() * 1000))

    class Meta:
        table_name = 't_task'
        indexes = (
            (('username', 'flow_type', 'flow_id', 'crontab'), True),
        )

    def save(self, *args, **kwargs):
        self.update_time = int(datetime.now().timestamp() * 1000)
        return super(TTask, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        """初始化表."""
        with db:
            if not cls.table_exists():
                db.create_tables([cls])

    @classmethod
    def get_user_tasks(cls, username: str) -> List['TTask']:
        """获取用户的所有任务.
        
        Args:
            username (str): 用户名
            
        Returns:
            List[TTask]: 任务列表
        """
        return cls.select().where(cls.username == username)

    @classmethod
    def check_task_exists(cls, username: str, flow_type: int, flow_id: str, crontab: str, exclude_task_id: Optional[int] = None) -> Tuple[bool, str]:
        """检查任务是否已存在.
        
        Args:
            username (str): 用户名
            flow_type (int): 流程类型
            flow_id (str): 流程ID
            crontab (str): crontab配置
            exclude_task_id (Optional[int], optional): 需要排除的任务ID. Defaults to None.
            
        Returns:
            Tuple[bool, str]: (是否存在, 错误信息)
        """
        query = cls.select().where(
            (cls.username == username) &
            (cls.flow_type == flow_type) &
            (cls.flow_id == flow_id) &
            (cls.crontab == crontab)
        )
        
        # 如果指定了需要排除的任务ID，则在查询中排除该任务
        if exclude_task_id is not None:
            query = query.where(cls.id != exclude_task_id)
            
        task = query.first()
        if task:
            return True, f"相同的任务配置已存在（流程ID: {flow_id}, 定时: {crontab}）"
        return False, ""

    @classmethod
    def create_task(cls, username: str, flow_type: int, flow_name: str, flow_id: str, crontab: str = '0 0 * * *') -> None:
        """创建新任务.
        
        Args:
            username (str): 用户名
            flow_type (int): 流程类型
            flow_name (str): 流程名称
            flow_id (str): 流程ID
            crontab (str, optional): crontab配置. Defaults to '0 0 * * *'.
            
        Raises:
            ValueError: 如果任务已存在
        """
        # 检查任务是否已存在
        exists, error_msg = cls.check_task_exists(username, flow_type, flow_id, crontab)
        if exists:
            raise ValueError(error_msg)
            
        cls.create(
            username=username,
            flow_type=flow_type,
            flow_name=flow_name,
            flow_id=flow_id,
            crontab=crontab
        )

    @classmethod
    def update_task_status(cls, task_id: int, status: int) -> None:
        """更新任务状态.
        
        Args:
            task_id (int): 任务ID
            status (int): 新状态 0-停止 1-运行中
        """
        task = cls.get_by_id(task_id)
        task.status = status
        task.save()

    @classmethod
    def update_task_crontab(cls, task_id: int, crontab: str) -> None:
        """更新任务定时配置.
        
        Args:
            task_id (int): 任务ID
            crontab (str): 新的crontab配置
            
        Raises:
            ValueError: 如果新的crontab配置与其他任务冲突
        """
        task = cls.get_by_id(task_id)
        
        # 如果crontab没有变化，直接返回
        if task.crontab == crontab:
            return
            
        # 检查新的crontab配置是否与其他任务冲突（排除当前任务）
        exists, error_msg = cls.check_task_exists(
            task.username,
            task.flow_type,
            task.flow_id,
            crontab,
            exclude_task_id=task_id
        )
        if exists:
            raise ValueError(error_msg)
            
        task.crontab = crontab
        task.save()

    @classmethod
    def delete_task(cls, task_id: int) -> None:
        """删除任务.
        
        Args:
            task_id (int): 任务ID
        """
        cls.delete_by_id(task_id)


# 重新初始化表
db.drop_tables([TTask])
TTask.init_table() 