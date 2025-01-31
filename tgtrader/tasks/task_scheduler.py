from typing import Dict, Optional, Any
import logging
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from tgtrader.dao.t_task import TTask
from tgtrader.dao.t_flow import FlowCfg

# 配置日志
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

class TaskScheduler:
    """
    任务调度器，负责管理和执行定时任务.
    
    使用APScheduler来调度任务，通过定期扫描任务表来管理任务的启动和停止.
    实现了单例模式，并处理系统信号以确保优雅关闭.
    
    Attributes:
        scheduler (BackgroundScheduler): APScheduler调度器实例
        running_jobs (Dict[int, str]): 正在运行的任务映射表，key为任务ID，value为job_id
    """
    
    _instance: Optional['TaskScheduler'] = None
    
    def __new__(cls) -> 'TaskScheduler':
        """单例模式实现."""
        if cls._instance is None:
            cls._instance = super(TaskScheduler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化任务调度器."""
        if not hasattr(self, 'initialized'):
            self.scheduler = BackgroundScheduler(
                jobstores={
                    'default': MemoryJobStore()
                },
                timezone='Asia/Shanghai'
            )
            self.running_jobs: Dict[int, str] = {}
            self._setup_signal_handlers()
            self.initialized = True
            
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
    def _handle_shutdown(self, signum: int, frame: Optional[object]) -> None:
        """处理关闭信号.
        
        Args:
            signum (int): 信号编号
            frame (Optional[object]): 当前栈帧
        """
        logging.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def start(self) -> None:
        """启动调度器并开始任务扫描."""
        # 启动调度器
        self.scheduler.start()
        logging.info("Task scheduler started")
        
        # 添加任务扫描job
        self.scheduler.add_job(
            func=self._scan_tasks,
            trigger='interval',
            seconds=30,  # 每30秒扫描一次任务表
            id='task_scanner',
            name='Task Scanner',
            replace_existing=True
        )
        logging.info("Task scanner started")
        
    def stop(self) -> None:
        """停止调度器."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("Task scheduler stopped")
            
    def _scan_tasks(self) -> None:
        """扫描任务表，同步任务运行状态."""
        try:
            # 获取所有任务
            all_tasks = TTask.select()
            
            # 获取当前运行的任务ID集合
            running_task_ids = set(self.running_jobs.keys())
            
            # 遍历所有任务
            for task in all_tasks:
                if task.id not in running_task_ids:
                    if task.status == 1:
                        # 数据库中是运行状态，但实际未运行的任务，启动它
                        self._add_job(task)
                else:
                    # 任务正在运行，检查crontab是否变更
                    job = self.scheduler.get_job(self.running_jobs[task.id])
                    if job:
                        current_crontab = str(job.trigger)
                        if current_crontab != task.crontab:
                            # crontab配置已变更，需要重新调度
                            logging.info(f"Task {task.id} crontab changed from {current_crontab} to {task.crontab}")
                            self._remove_job(task.id)
                            if task.status == 1:
                                self._add_job(task)
                    
                    # 检查运行状态
                    if task.status == 0:
                        # 数据库中是停止状态，但实际在运行的任务，停止它
                        self._remove_job(task.id)
                    
            # 清理已删除的任务
            for task_id in list(running_task_ids):
                try:
                    TTask.get_by_id(task_id)
                except:
                    # 任务已从数据库中删除，停止它
                    self._remove_job(task_id)
                    
        except Exception as e:
            logging.error(f"Failed to scan tasks: {str(e)}")
            
    def _add_job(self, task: TTask) -> None:
        """添加任务到调度器.
        
        Args:
            task (TTask): 任务配置
        """
        if task.id in self.running_jobs:
            return
            
        try:
            # 创建cron触发器
            trigger = CronTrigger.from_crontab(task.crontab)
            
            # 添加任务到调度器
            job = self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[task.id],
                id=f"task_{task.id}",
                name=f"{task.flow_name}_{task.flow_id}",
                replace_existing=True
            )
            
            self.running_jobs[task.id] = job.id
            logging.info(f"Added task {task.flow_name} (ID: {task.id}) with schedule: {task.crontab}")
            
        except Exception as e:
            logging.error(f"Failed to add task {task.id}: {str(e)}")
            
    def _remove_job(self, task_id: int) -> None:
        """从调度器中移除任务.
        
        Args:
            task_id (int): 任务ID
        """
        job_id = self.running_jobs.get(task_id)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                del self.running_jobs[task_id]
                logging.info(f"Removed task {task_id}")
            except Exception as e:
                logging.error(f"Failed to remove task {task_id}: {str(e)}")
                
    def _execute_task(self, task_id: int) -> None:
        """执行任务.
        
        Args:
            task_id (int): 任务ID
        """
        try:
            task = TTask.get_by_id(task_id)
            flow = FlowCfg.get_by_id(task.flow_id)
            
            # TODO: 实现具体的任务执行逻辑
            logging.info(f"Executing task {task.flow_name} (ID: {task.id}) at {datetime.now()}")
            
            # 这里需要根据实际情况调用相应的流程执行函数
            # flow.execute() 或其他执行方法
            
        except Exception as e:
            logging.error(f"Failed to execute task {task_id}: {str(e)}")

    @classmethod
    def run_service(cls) -> None:
        """运行任务服务的主函数."""
        scheduler = cls()
        scheduler.start()
        
        # 保持主线程运行
        try:
            signal.pause()
        except (KeyboardInterrupt, SystemExit):
            scheduler.stop()

if __name__ == '__main__':
    TaskScheduler.run_service() 