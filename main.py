from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import time
import configparser

print('\n--正在初始化--\n')

#连接参数配置
cfg = configparser.ConfigParser()
cfg.read("config.ini", encoding="utf-8")

host = cfg.get("mysql", "host")
user = cfg.get("mysql", "user")
password = cfg.get("mysql", "password")
database = cfg.get("mysql", "db_name")
engine = create_engine("mysql+mysqlconnector://{}:{}@{}/{}"
                       .format(user, password, host, database)
                       )
con_db = engine.connect()

# 默认值
initial_value= cfg.getint("params", "init_id")
step_size= cfg.getint("params", "step")
total_rows= cfg.getint("params", "total_rows")
TS_MIN = cfg.getint("params", "ts_min")
TS_MAX = cfg.getint("params", "ts_max")
current_start = initial_value
Value_Id_Behavior = tuple(cfg.get("params", "valid_behavior").split(','))
total_month = pd.DataFrame(columns=['month', "用户量","浏览量", "加购", "收藏", "购买","新用户数","老用户数"])
total_days = pd.DataFrame(columns=["用户量","浏览量", "加购", "收藏", "购买","新用户数","老用户数"])
month_list = []
day_list = []

time.sleep(2)
print('\n--正在查询数据库--\n--预计时长约5分钟、请耐心等待--\n')
start_time = time.perf_counter()

# 查新老用户
# 创建临时表，放用户总数
create_tmp_sql = text("""
CREATE TEMPORARY TABLE tmp_user_buy AS 
SELECT user_id,SUM(IF(behavior='buy',1,0)) total_buy 
FROM userbehavior GROUP BY user_id;
""")
con_db.execute(create_tmp_sql)
con_db.commit()
# 从临时表生成用户标签df
user_tag_sql = """
SELECT user_id,CASE WHEN total_buy<=1 THEN '新用户' ELSE '老用户' END user_tag
FROM tmp_user_buy;
"""
df_user_type = pd.read_sql(user_tag_sql,con_db)
end_time = time.perf_counter()

print(f"\n本次查询总耗时：{end_time-start_time:.6f}秒\n")
time.sleep(2)

# 循环判断
while current_start <= total_rows:
    current_end = current_start + step_size - 1
    if current_end > total_rows:
        current_end = total_rows
    # sql语句拼接
    querty = f"""select * from userbehavior 
                 where id between {str(current_start)} and {str(current_end)}
                 and ts is not Null
                 and ts between {str(TS_MIN)} and {str(TS_MAX)}
                 and behavior in ('pv', 'cart', 'fav', 'buy');
                 
              """
    # 查询
    df = pd.read_sql(querty, con_db)
    df = pd.merge(df, df_user_type, on="user_id", how="left")


    # 去重，去空行
    df = df.drop_duplicates()
    df = df.dropna()
    # 无操作跳过
    if df.empty:
        print(f"[{current_start}~{current_end}]无数据")
        current_start = current_end + 1
        continue
    # 时间戳改为新列日期，加入月份
    df['datetime']=pd.to_datetime(df['ts'], unit='s')
    df['month'] = df['datetime'].dt.to_period('M')
    df['days'] = df['datetime'].dt.date
    # 按月分组
    month_agg = df.groupby('month').apply(
        lambda x: pd.Series({
            '用户量': x['user_id'].nunique(),
            '浏览量': (x['behavior'] == 'pv').sum(),
            '加购': (x['behavior'] == 'cart').sum(),
            '收藏': (x['behavior'] == 'fav').sum(),
            '购买': (x['behavior'] == 'buy').sum(),
            '新用户数': x[x['user_tag'] == '新用户']['user_id'].nunique(),
            '老用户数': x[x['user_tag'] == '老用户']['user_id'].nunique()
        })
    ).reset_index()
    day_agg = df.groupby('days').apply(
        lambda x: pd.Series({
            '用户量': x['user_id'].nunique(),
            '浏览量': (x['behavior'] == 'pv').sum(),
            '加购': (x['behavior'] == 'cart').sum(),
            '收藏': (x['behavior'] == 'fav').sum(),
            '购买': (x['behavior'] == 'buy').sum(),
            '新用户数': x[x['user_tag'] == '新用户']['user_id'].nunique(),
            '老用户数': x[x['user_tag'] == '老用户']['user_id'].nunique()
        })
    ).reset_index()
    month_list.append(month_agg)
    day_list.append(day_agg)

    # 下一批
    print(f"处理完成：{current_start} ~ {current_end}")
    current_start = current_end + 1
    # 合并结果
    total_month = pd.concat(month_list).groupby('month').sum().reset_index()
    total_days = pd.concat(day_list).groupby('days').sum().reset_index()
    # 数据排序
    total_days = total_days.sort_values("days").reset_index(drop=True)
    total_month = total_month.sort_values("month").reset_index(drop=True)
# 打印结果，关闭连接
print('月度统计结果为\n',total_month)
print('每日统计结果为\n',total_days)
con_db.close()

#按月统计结果open写入txt
with open("monthly_stat.txt", "w", encoding="utf-8") as f:
    # 写入表头
    f.write("月份\t用户量\t浏览量\t加购\t收藏\t购买\t新用户数\t老用户数\n")
    # 逐行写入数据
    for _, row in total_month.iterrows():
        line = f"{row['month']}\t{row['用户量']}\t{row['浏览量']}\t{row['加购']}\t{row['收藏']}\t{row['购买']}\t{row['新用户数']}\t{row['老用户数']}\n"
        f.write(line)

# 按日统计结果open写入txt
with open("daily_stat.txt", "w", encoding="utf-8") as f:
    f.write("日期\t用户量\t浏览量\t加购\t收藏\t购买\t新用户数\t老用户数\n")
    for _, row in total_days.iterrows():
        line = f"{row['days']}\t{row['用户量']}\t{row['浏览量']}\t{row['加购']}\t{row['收藏']}\t{row['购买']}\t{row['新用户数']}\t{row['老用户数']}\n"
        f.write(line)

print("   txt文件写入完成：")
print("   月度数据：monthly_stat.txt")
print("   日度数据：daily_stat.txt")

# 替代 open 直接写入csv文件
total_month.to_csv("monthly_stat.csv", sep=",", index=False, encoding="utf-8-sig")
total_days.to_csv("daily_stat.csv", sep=",", index=False, encoding="utf-8-sig")
print("   Excel文件写入完成：")
print("   月度数据：monthly_stat.csv")
print("   日度数据：daily_stat.csv")

time.sleep(2)
print('\n数据查询完成！')
