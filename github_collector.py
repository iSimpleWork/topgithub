import sqlite3
import requests
from datetime import datetime, timedelta
import logging
import time
from models import Database
from const import DB_NAME

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GithubCollector:
    def __init__(self):
        self.api_base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GithubTrendingCollector"
        }

    def _make_request(self, url, params=None):
        """发送请求并处理响应"""
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # 检查 API 限制
            remaining = response.headers.get('X-RateLimit-Remaining', '0')
            logger.info(f"API 剩余请求次数: {remaining}")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {str(e)}")
            raise

    def collect_trending_repos(self):
        """获取趋势项目数据"""
        try:
            search_url = f"{self.api_base_url}/search/repositories"
            params = {
                'q': f'stars:>100',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 100
            }
            
            logger.info("开始获取趋势项目数据...")
            data = self._make_request(search_url, params)
            
            if 'items' not in data:
                logger.error("API返回数据格式不正确")
                return []
                
            repos = data['items']
            logger.info(f"成功获取 {len(repos)} 个项目数据")
            
            # 打印项目信息
            for repo in repos:
                logger.info(f"""
                项目名称: {repo.get('full_name')}
                描述: {repo.get('description', 'N/A')}
                URL: {repo.get('html_url')}
                Stars: {repo.get('stargazers_count', 0)}
                创建时间: {repo.get('created_at')}
                """)
            # 将项目数据存入数据库

            db = Database()
            
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                collect_date = datetime.now().strftime('%Y-%m-%d')
                
                for repo in repos:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO github_project (
                                project_id, repo_id, name, full_name, description,
                                url, language, collect_date, stars, forks, watchers
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            repo.get('id'),
                            str(repo.get('full_name')), 
                            repo.get('name'),
                            repo.get('full_name'),
                            repo.get('description'),
                            repo.get('html_url'),
                            repo.get('language'),
                            collect_date,
                            repo.get('stargazers_count', 0),
                            repo.get('forks_count', 0), 
                            repo.get('watchers_count', 0)
                        ))
                        
                        
                    except sqlite3.Error as e:
                        logger.error(f"存储项目 {repo.get('full_name')} 数据时出错: {str(e)}")
                        continue
                        
                conn.commit()
                logger.info("成功将项目数据存入数据库")
            return repos
                
        except Exception as e:
            logger.error(f"获取数据时出错: {str(e)}")
            return []

    def update_history(self):
        """更新历史数据"""
        """更新历史数据"""
        logger.info("开始更新历史数据...")
        
        try:
            db = Database()
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取总记录数
                cursor.execute('SELECT COUNT(*) FROM github_project')
                total_count = cursor.fetchone()[0]
                
                # 计算总页数
                page_size = 100
                total_pages = (total_count + page_size - 1) // page_size
                
                collect_date = datetime.now().strftime('%Y-%m-%d')
                
                for page in range(total_pages):
                    offset = page * page_size
                    
                    # 分页查询项目ID
                    cursor.execute('''
                        SELECT project_id FROM github_project 
                        LIMIT ? OFFSET ?
                    ''', (page_size, offset))
                    
                    repo_ids = [row[0] for row in cursor.fetchall()]
                    logger.info(f"正在处理第 {page + 1}/{total_pages} 页, {len(repo_ids)} 个项目")
                    
                    # 获取最新数据
                    repo_details = self.get_repo_details(repo_ids)
                    
                    logger.info(f"第 {page + 1} 页数据更新完成")
                    
                logger.info("所有历史数据更新完成")
                
        except Exception as e:
            logger.error(f"更新历史数据时出错: {str(e)}")
        pass

    def get_repo_details(self, repo_ids):
        """获取指定仓库的详细信息"""
        try:
            db = Database()
            logger.info(f"开始获取 {len(repo_ids)} 个项目的详细数据")
            repo_details = []
            
            for repo_id in repo_ids:
                try:
                    repo_url = f"{self.api_base_url}/repositories/{repo_id}"
                    repo = self._make_request(repo_url)
                    
                    logger.info(f"""
                    获取项目详情:
                    ID: {repo.get('project_id')}
                    名称: {repo.get('full_name')}
                    Stars: {repo.get('stargazers_count', 0)}
                    """)
                    # 将数据写入历史表
                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO github_project_history 
                            (project_id, stars, forks, watchers, collect_date)
                            VALUES (?, ?, ?, ?, datetime('now'))
                        ''', (
                            repo.get('id'),
                            repo.get('stargazers_count', 0),
                            repo.get('forks_count', 0), 
                            repo.get('watchers_count', 0)
                        ))
                        conn.commit()
                    repo_details.append(repo)
                    time.sleep(1)  # 简单延时
                    
                except Exception as e:
                    logger.error(f"获取项目 {repo_id} 详情时出错: {str(e)}")
                    continue
            
            return repo_details
                
        except Exception as e:
            logger.error(f"获取详细数据时出错: {str(e)}")
            return []

# 使用示例
if __name__ == "__main__":
    collector = GithubCollector()
    
    # 获取趋势项目
    trending_repos = collector.get_trending_repos()
    
    # 获取前5个项目的详细信息
    if trending_repos:
        repo_ids = [repo['id'] for repo in trending_repos[:5]]
        repo_details = collector.get_repo_details(repo_ids)