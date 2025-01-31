# encoding: utf-8
import streamlit as st
import arrow
from tgtrader.dao.t_task import TTask
from tgtrader.dao.t_flow import FlowCfg
from tgtrader.streamlit_pages.utils.common import get_user_name


def get_crontab_description(crontab: str) -> str:
    """将crontab表达式转换为人类可读的描述.
    
    Args:
        crontab (str): crontab表达式
        
    Returns:
        str: 人类可读的描述
    """
    parts = crontab.split()
    if len(parts) != 5:
        return "无效的crontab表达式"
    
    minute, hour, day, month, week = parts
    
    if minute == "0" and hour == "0" and day == "*" and month == "*" and week == "*":
        return "每天0点执行"
    elif minute == "0" and hour == "*" and day == "*" and month == "*" and week == "*":
        return "每小时执行"
    elif minute == "*" and hour == "*" and day == "*" and month == "*" and week == "*":
        return "每分钟执行"
    else:
        return f"定时: {crontab}"


def run():
    """任务管理页面."""
    st.header("任务管理")
    
    # 获取当前用户
    username = get_user_name()
    if not username:
        st.error("请先登录")
        return

    # 添加新任务按钮
    with st.expander("添加新任务"):
        # 获取所有流程类型和名称
        flows = FlowCfg.select().where(FlowCfg.username == username)
        flow_types = sorted(list(set([flow.flow_type for flow in flows])))
        
        # 流程类型下拉框
        flow_type = st.selectbox("流程类型", flow_types)
        
        # 根据选择的流程类型过滤流程名称
        filtered_flows = [flow for flow in flows if flow.flow_type == flow_type]
        flow_names = [flow.flow_name for flow in filtered_flows]
        flow_name_idx = st.selectbox("流程名称", range(len(flow_names)), format_func=lambda x: flow_names[x])
        flow_name = flow_names[flow_name_idx]
        flow_id = filtered_flows[flow_name_idx].flow_id
        
        # crontab配置
        st.markdown("##### 定时配置")
        crontab_type = st.radio(
            "执行频率",
            ["每天执行", "每小时执行", "每分钟执行", "自定义"],
            horizontal=True
        )
        
        if crontab_type == "每天执行":
            crontab = "0 0 * * *"
        elif crontab_type == "每小时执行":
            crontab = "0 * * * *"
        elif crontab_type == "每分钟执行":
            crontab = "* * * * *"
        else:
            crontab = st.text_input("Crontab表达式", value="0 0 * * *", help="分 时 日 月 周")
        
        if st.button("保存"):
            if flow_type and flow_name:
                try:
                    TTask.create_task(
                        username=username,
                        flow_type=flow_type,
                        flow_name=flow_name,
                        flow_id=flow_id,
                        crontab=crontab
                    )
                    st.success(f"任务已创建")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            else:
                st.error("请选择流程类型和流程名称")

    # 显示现有任务
    st.subheader("任务列表")
    
    # 从数据库获取任务
    tasks = TTask.get_user_tasks(username=username)
    
    if tasks:
        # 使用2列布局显示任务卡片
        cols = st.columns(2)
        for i, task in enumerate(tasks):
            with cols[i % 2]:
                # 创建任务卡片
                with st.container():
                    # 设置卡片样式
                    st.markdown("""
                    <style>
                    .task-card {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                        background-color: white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .task-header {
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 12px;
                        color: #1f1f1f;
                    }
                    .task-info {
                        font-size: 14px;
                        color: #666;
                        margin-bottom: 8px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .task-status {
                        font-weight: bold;
                        padding: 4px 8px;
                        border-radius: 4px;
                        background-color: #f0f0f0;
                    }
                    .task-status.running {
                        color: #28a745;
                        background-color: #e6f4ea;
                    }
                    .task-status.stopped {
                        color: #dc3545;
                        background-color: #fbe9e7;
                    }
                    .task-time {
                        color: #888;
                        font-size: 12px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    status_class = "running" if task.status == 1 else "stopped"
                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-header">{task.flow_name}</div>
                        <div class="task-info">
                            <span>流程类型: {task.flow_type}</span>
                            <span class="task-status {status_class}">{"运行中" if task.status == 1 else "停止"}</span>
                        </div>
                        <div class="task-info">
                            <span>执行计划: {get_crontab_description(task.crontab)}</span>
                        </div>
                        <div class="task-time">
                            创建: {arrow.get(task.create_time/1000, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss')}
                            <br/>
                            更新: {arrow.get(task.update_time/1000, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 操作按钮 - 右对齐布局
                    _, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col2:
                        if task.status == 0:
                            if st.button("启动", key=f"start_{task.id}", type="primary"):
                                TTask.update_task_status(task.id, 1)
                                st.success("任务已启动")
                                st.rerun()
                        else:
                            if st.button("停止", key=f"stop_{task.id}", type="secondary"):
                                TTask.update_task_status(task.id, 0)
                                st.success("任务已停止")
                                st.rerun()
                    
                    with col3:
                        if st.button("编辑", key=f"edit_{task.id}"):
                            st.session_state.editing_task = True
                            st.session_state.editing_task_id = task.id
                            st.session_state.editing_task_crontab = task.crontab
                    
                    with col4:
                        if st.button("删除", key=f"delete_{task.id}", type="secondary"):
                            TTask.delete_task(task.id)
                            st.success("任务已删除")
                            st.rerun()
            
        # 如果处于编辑状态，显示编辑表单
        if st.session_state.get('editing_task', False):
            with st.form("编辑任务"):
                st.subheader("编辑定时配置")
                
                # crontab配置
                st.markdown("##### 定时配置")
                crontab_type = st.radio(
                    "执行频率",
                    ["每天执行", "每小时执行", "每分钟执行", "自定义"],
                    horizontal=True,
                    key="edit_crontab_type"
                )
                
                if crontab_type == "每天执行":
                    edited_crontab = "0 0 * * *"
                elif crontab_type == "每小时执行":
                    edited_crontab = "0 * * * *"
                elif crontab_type == "每分钟执行":
                    edited_crontab = "* * * * *"
                else:
                    edited_crontab = st.text_input(
                        "Crontab表达式",
                        value=st.session_state.editing_task_crontab,
                        help="分 时 日 月 周"
                    )
                
                # 提交和取消按钮
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("保存修改")
                with col2:
                    cancel = st.form_submit_button("取消")
                
                if submit:
                    try:
                        TTask.update_task_crontab(st.session_state.editing_task_id, edited_crontab)
                        st.success("定时配置更新成功")
                        st.session_state.editing_task = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新定时配置失败: {str(e)}")
                
                if cancel:
                    st.session_state.editing_task = False
                    st.rerun()
    else:
        st.info("当前没有任何任务")

