# 电商用户行为数据分析工具
基于 MySQL + Python 实现的海量用户行为数据统计与分析工具，支持大表分片处理、用户分层、多维度指标计算，自动生成日/月度报表，可直接用于 Excel 可视化与业务分析。

## 项目功能
- 海量用户行为数据按 ID 分段查询，避免内存溢出
- 数据清洗：去重、空值过滤、异常时间与行为过滤
- 按日/按月统计：用户量、浏览量、加购量、收藏量、购买量
- 新老用户自动分层：0–1 次购买为新用户，≥2 次为老用户
- 输出日度/月度统计报表：TXT + CSV 双格式
- 配置文件分离，隐私信息不上传仓库

## 技术栈
- Python 3
- Pandas
- SQLAlchemy
- MySQL
- ConfigParser

## 指标口径
- 浏览量(pv)、加购量(cart)、收藏量(fav)、购买量(buy)
- 用户量：去重 user_id
- 新用户：全周期购买次数 = 0 或 1
- 老用户：全周期购买次数 ≥ 2

## 使用步骤
1. 克隆本仓库
2. 复制 `config.ini.example` 并重命名为 `config.ini`
3. 在 `config.ini` 中填写 MySQL 连接信息
4. 安装依赖：
pip install pandas sqlalchemy mysql-connector-python
5. 运行：
python main.py
6. 查看输出文件：
- daily_stat.txt / daily_stat.csv
- monthly_stat.txt / monthly_stat.csv

## 文件说明
- main.py：主程序，数据查询、清洗、聚合、输出
- config.ini.example：数据库配置模板
- .gitignore：忽略配置文件、缓存、输出报表
- 查询工具使用说明.pdf：详细使用步骤
- 查询工具用途展示.pdf：效果展示

## 项目亮点
- 支持亿级大表安全分片处理，不崩内存
- 新老用户自动标记，无需手动干预
- 输出文件日期有序，可直接生成图表
- 配置与代码分离，安全上传 GitHub
- 代码简洁规范，适合学习与简历展示