import requests
import json
import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import schedule
import time


class GithubStarTracker:
    def __init__(self, db_path='github_stars.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS star_history
                    (repo_name TEXT, star_count INTEGER, 
                     record_date DATE,
                     PRIMARY KEY (repo_name, record_date))''')
        conn.commit()
        conn.close()

    def get_repo_stars(self, repo_name):
        """获取指定仓库的star数"""
        url = f'https://api.github.com/repos/{repo_name}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()['stargazers_count']
            else:
                print(f"获取{repo_name}的star数失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None

    def record_stars(self, repo_list):
        """记录多个仓库的star数"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        today = datetime.date.today()

        for repo in repo_list:
            stars = self.get_repo_stars(repo)
            if stars is not None:
                c.execute('''INSERT OR REPLACE INTO star_history 
                           (repo_name, star_count, record_date)
                           VALUES (?, ?, ?)''',
                          (repo, stars, today))
                print(f"记录 {repo} 的star数: {stars}")

        conn.commit()
        conn.close()

    def plot_history(self, repo_name):
        """绘制指定仓库的star数历史折线图"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''SELECT record_date, star_count 
                    FROM star_history 
                    WHERE repo_name = ?
                    ORDER BY record_date''', (repo_name,))

        dates = []
        stars = []
        for row in c.fetchall():
            dates.append(datetime.datetime.strptime(row[0], '%Y-%m-%d').date())
            stars.append(row[1])

        conn.close()

        if not dates:
            print(f"没有找到 {repo_name} 的历史数据")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(dates, stars, marker='o')
        plt.title(f'{repo_name} Star History')
        plt.xlabel('Date')
        plt.ylabel('Stars')
        plt.grid(True)

        plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        plt.gcf().autofmt_xdate()

        plt.tight_layout()
        plt.show()


def daily_task(tracker, repos):
    """每日任务"""
    print(f"开始记录 {datetime.datetime.now()}")
    tracker.record_stars(repos)


def main():
    # 初始化跟踪器
    tracker = GithubStarTracker()

    # 要跟踪的仓库列表
    repos = [
        'tensorflow/tensorflow',
        'pytorch/pytorch',
        'microsoft/vscode'
        # 添加更多想要跟踪的仓库
    ]

    # 设置每日定时任务
    schedule.every().day.at("00:00").do(daily_task, tracker, repos)

    # 先执行一次
    daily_task(tracker, repos)

    # 持续运行定时任务
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("程序已停止")


if __name__ == "__main__":
    main()
