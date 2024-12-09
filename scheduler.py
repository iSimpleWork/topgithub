from apscheduler.schedulers.background import BackgroundScheduler
from github_collector import GithubCollector
def trigger_manual_collection():
    """手动触发一次数据采集和历史更新"""
    collector = GithubCollector()
    print("开始手动数据采集...")
    collector.collect_trending_repos()
    print("数据采集完成,开始更新历史数据...")
    collector.update_history()
    print("历史数据更新完成")

def init_scheduler():
    scheduler = BackgroundScheduler()
    collector = GithubCollector()
    
    # 每天凌晨2点执行数据采集
    scheduler.add_job(collector.collect_trending_repos, 'cron', hour=2)
    # 每天凌晨3点执行历史数据更新
    scheduler.add_job(collector.update_history, 'cron', hour=3)
    
    scheduler.start() 