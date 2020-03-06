import os
from utils import load_yaml
import pymysql

# 连接数据库
cf_dict = load_yaml('./config.yaml')
login_cf = cf_dict['login_config'][0]
db = connect_mysql(login_cf)
cursor = db.cursor(cursor=pymysql.cursors.SSDictCursor)



# cursor.execute('select pd_img_mark_info.img_id,max(pd_img_mark_info.mark_time) '
#                'from pd_img_mark_info '
#                'group by pd_img_mark_info.img_id '
#                'order by img_id')

# cursor.execute('select img_id,img_path,markfile_path,'
#                'pd_task_info.org_id, pd_task_info.viscera,pd_task_info.task_status '
#                'from pd_img_info inner join pd_task_info '
#                'on pd_img_info.task_id =pd_task_info.task_id '
#                'and task_status in (3,4)')

# cursor.execute('select pd_img_info.img_id, pd_img_info.img_path, pd_img_mark_info.mark_time '
#                'from pd_img_info inner join pd_img_mark_info '
#                'on pd_img_info.img_id = pd_img_mark_info.img_id')

task_id_list = []
search_dict = cursor.fetchall()
# print(search_dict)
for item in search_dict:
    print(item)


print(len(search_dict))
print(len(task_id_list))
print('hi')

a = search_dict[0]['img_path']
# if a.strip().split('.')[-1] == 'mrxs':
#
# else:
