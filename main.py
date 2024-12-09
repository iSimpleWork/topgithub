from app import app
from scheduler import init_scheduler, trigger_manual_collection

if __name__ == '__main__':
    # 启动定时任务
    init_scheduler()
    # 手动触发一次数据采集和历史更新
    #trigger_manual_collection()
    # 启动Web服务
    app.run(host='127.0.0.1', port=5000, debug=True)