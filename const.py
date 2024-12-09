import os  # 添加这一行

# GitHub API 相关常量
TOP_REPOS_LIMIT = 20  # 获取趋势项目的数量

# 数据库相关常量
DB_NAME = 'github.db'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_NAME)

# Star历史数据库相关常量
STAR_HISTORY_DB = 'github_stars.db'
STAR_HISTORY_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), STAR_HISTORY_DB)
