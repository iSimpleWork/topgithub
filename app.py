from flask import Flask, render_template, request
from db import get_db
import json
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    # 获取查询参数
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))  # 默认每页20条

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 添加日志输出，帮助调试
            print(f"查询日期: {selected_date}")
            
            # 获取总记录数
            cursor.execute('SELECT COUNT(*) FROM github_project WHERE collect_date = ?', 
                         (selected_date,))
            total_items = cursor.fetchone()[0]
            print(f"- 总记录数: {total_items}")
            # 如果没有数据，直接返回空结果
            if total_items == 0:
                return render_template('index.html',
                                    projects=[],
                                    selected_date=selected_date,
                                    current_page=1,
                                    per_page=per_page,
                                    total_pages=1,
                                    total_items=0)

            # 确保页码有效
            total_pages = (total_items + per_page - 1) // per_page
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages
            offset = (page - 1) * per_page

            # 获取分页数据
            cursor.execute('''
                SELECT * FROM github_project 
                WHERE collect_date = ? 
                ORDER BY stars DESC 
                LIMIT ? OFFSET ?
            ''', (selected_date, per_page, offset))
            projects = cursor.fetchall()
            # 打印项目列表信息
            print(f"查询结果: 共{len(projects)}条记录")
            for project in projects:
                print(json.dumps(project))

            return render_template('index.html',
                                projects=projects,
                                selected_date=selected_date,
                                current_page=page,
                                per_page=per_page,
                                total_pages=total_pages,
                                total_items=total_items)
    except Exception as e:
        # 改进错误处理，添加更详细的错误信息
        import traceback
        print(f"数据库查询错误: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        
        return render_template('index.html',
                            projects=[],
                            selected_date=selected_date,
                            current_page=1,
                            per_page=per_page,
                            total_pages=1,
                            total_items=0,
                            error_message=f"发生错误: {str(e)}")  # 添加错误信息到模板

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    with get_db() as conn:
        cursor = conn.cursor()
        # 获取项目基本信息
        cursor.execute('SELECT * FROM github_project WHERE project_id = ?', (project_id,))
        project = cursor.fetchone()
        #print(json.dumps(project))
        # 获取历史数据
        cursor.execute('''
            SELECT collect_date, stars, forks, watchers 
            FROM github_project_history 
            WHERE project_id = ? 
            AND collect_date >= date('now', '-3 months')
            ORDER BY collect_date
        ''', (project_id,))
        history = cursor.fetchall()
        print(json.dumps(history))
    return render_template('project_detail.html', 
                         project=project, 
                         history=json.dumps(history))

@app.route('/admin/database')
def db_admin():
    # 获取所有表名
    cursor = get_db().cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(json.dumps(tables))
    return render_template('db_admin.html', tables=tables)

@app.route('/admin/database/table/<table_name>')
def table_structure(table_name):
    cursor = get_db().cursor()
    # 获取表结构
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    columns = cursor.fetchall()
    # 获取表的前10条数据作为预览
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
    sample_data = cursor.fetchall()
    return render_template('table_structure.html', 
                         table_name=table_name, 
                         columns=columns, 
                         sample_data=sample_data) 