import paramiko
import os
from utils import load_yaml, dump_yaml, add_yaml, progress_bar, easy_bar
from dataInfo import MysqlDeal
import time
from tqdm import tqdm


class ParamikoClient:
    def __init__(self, cf_file, info_file, log_file, root_path):
        self.config_path = cf_file  # config文件的地址（服务器和数据库的地址）
        self.info_path = info_file  # info 文件的地址（数据库中的数据）
        self.log_path = log_file  # log文件的地址 （更新日志）
        self.root_path = root_path  # 服务器的同步地址
        cf_dict = load_yaml(cf_file)
        self.client = paramiko.SSHClient()
        # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.remote_cf = cf_dict['remote_config'][0]
        self.sftp_client = None
        self.client_state = 0  # server是否已经连接上的标志，0：没有，1：已连接
        self.succeed_count = 0  # 当日已完成的更新数量
        self.total_count = 0  # 当日需要完成的更新总数

    def connect(self):
        """
        连接server
        :return:
        """
        try:
            self.client.connect(hostname=self.remote_cf['host'],
                                port=self.remote_cf['port'],
                                username=self.remote_cf['username'],
                                password=self.remote_cf['password'],
                                timeout=self.remote_cf['timeout'])
            self.client_state = 1
        except Exception as e:
            print(e)
            self.client.close()

    def run_cmd(self, cmd_str):
        """
        测试用
        :param cmd_str:
        :return:
        """
        if self.client_state == 0:
            self.connect()
        stdin, stdout, stderr = self.client.exec_command(cmd_str)

        return stdout.readline()

    def path_confirm(self, path):
        """
        检查server中path是否存在，如果不存在，就创建一个新目录
        :param path: 目录所在地址
        :return:
        """
        if self.client_state == 0:
            self.connect()
        if not self.sftp_client:
            self.sftp_client = paramiko.SFTPClient.from_transport(self.client.get_transport())
        try:
            self.sftp_client.stat(path)
        except IOError:
            self.sftp_client.mkdir(path)

    def path_exist(self, path):
        """
        检测server中path是否存在，如果不存在，返回false
        :param path:
        :return:
        """
        flag = True
        if self.client_state == 0:
            self.connect()
        if not self.sftp_client:
            self.sftp_client = paramiko.SFTPClient.from_transport(self.client.get_transport())
        try:
            self.sftp_client.stat(path)
        except IOError:
            # self.sftp_client.mkdir(path)
            flag = False

        return flag

    def upload_file(self, root_dir, item):
        """
        根据数据信息，将文件上传到server中，方式：一条一条传
        :param root_dir: server中文件所在的根目录
        :param item: 一条数据（字典）
        :return:
        """
        whole_name = root_dir
        img_upload_state = 0 # 文件上传的状态，0：失败，1：成功
        xml_upload_state = 0 # 标注上传的状态，0：失败，1：成功
        if not item['img_path'].split('.')[-1] == 'mrxs':

            # 上传xml
            whole_name = root_dir
            for name in item['markfile_path'].split('/')[:-1][1:]:
                whole_name = os.path.join(whole_name,name)
                self.path_confirm(whole_name)
            try:
                self.sftp_client.put('/iapsfile' + item['markfile_path'],
                                     whole_name + item['markfile_path'].split('/')[-1],
                                     callback=progress_bar)
                xml_upload_state = 1
            except Exception as e:
                self.check_and_update_log(log_path=self.log_path,
                                          s_count=self.succeed_count,
                                          all_count=self.total_count)  # 当出现异常，直接写log日志，记录当日失败情况
                print(e)

            # 上传img
            for name in item['img_path'].split('/')[:-1]:
                whole_name = whole_name + name + '/'
                self.path_confirm(whole_name)
            try:
                self.sftp_client.put('/iapsfile' + item['img_path'], whole_name + item['img_path'].split('/')[-1],
                                     callback=progress_bar)
                img_upload_state = 1
            except Exception as e:
                self.check_and_update_log(log_path=self.log_path,
                                          s_count=self.succeed_count,
                                          all_count=self.total_count)  # 当出现异常，直接写log日志，记录当日失败情况
                print(e)  # 当出现异常，将异常记录到yaml文件（此句需要修改）

        return xml_upload_state * img_upload_state

    def check_and_update_log(self, log_path, s_count, all_count):
        """
        所有更新完成后,检查文件,并写log
        :param log_path: 日志所在的路径
        :param s_count: 成功更新的文件数量
        :param all_count: 当日需要更新的文件数量
        :return:
        """
        if s_count == all_count:
            record = {
                'Update time': self.run_cmd('date'),
                'Successfully update': s_count,
                'Total': all_count
            }
            sp = '---------------------'
            add_yaml(log_path, sp)
            add_yaml(log_path, record)
            add_yaml(log_path, sp)
        else:
            record = {
                'Update time': self.run_cmd('date'),
                'Successfully update': s_count,
                'Failed update': all_count - s_count,
                'Total': all_count
            }
            sp = '---------------------'
            add_yaml(log_path, sp)
            add_yaml(log_path, record)
            add_yaml(log_path, sp)

    def get_sync(self, i):
        """
        进行数据同步
        :param i:
        :param root_dir: server端的根目录，用于存储img和xml
        :return:
        """
        if self.client_state == 0:
            self.connect()
        if not self.sftp_client:
            self.sftp_client = paramiko.SFTPClient.from_transport(self.client.get_transport())
            # if not self.sftp_client.listdir(root_dir):
            mysql = MysqlDeal(config_yaml=self.config_path, info_yaml=self.info_path)
            new_db = mysql.check_update(i=i)
            self.total_count = len(new_db)
            print('Num of files need to update:{}'.format(len(new_db)))
            if new_db is not None:
                # 判断当日是否需要更新
                for item in new_db:
                    # item = new_db[0]  # 只取第一个数据做测试（全部测试速度太慢）
                    if self.upload_file(root_dir=self.root_path, item=item):
                        self.succeed_count += 1
                        add_yaml(self.info_path, [item])
                self.check_and_update_log(log_path=self.log_path,
                                          s_count=self.succeed_count,
                                          all_count=self.total_count)  # 所有成功更新，更新日志

    def one_item(self, i, img_path, xml_path):
        """
        同步指定的一项数据，用于测试
        Usage:
            >>> one_iem(i=4, img_pat='', xml_path='')

        """
        if self.client_state == 0:
            self.connect()
        if not self.sftp_client:
            self.sftp_client = paramiko.SFTPClient.from_transport(self.client.get_transport())
            # if not self.sftp_client.listdir(root_dir):
            mysql = MysqlDeal(config_yaml=self.config_path, info_yaml=self.info_path)
            new_db = mysql.check_update(i=i)
            self.total_count = len(new_db)
            print(self.total_count)
            # one_file = new_db[0]
            # print(one_file)
            tianjing_list = []
            for i in new_db:
                if i['org_id'] is 13:
                    tianjing_list.append(i)
            print(len(tianjing_list))
            one_file = tianjing_list[1]
            print(one_file)
            # print(mysql)
            # ll = self.upload_file(root_dir=img_path, item=one_file)
            # print('Finished:｛｝'.format(ll))
            # print(one_file['markfile_path'].split('/')[-1])
            local_path = '/iapsfile' + one_file['markfile_path']
            remote_path = img_path + one_file['markfile_path'].split('/')[-1]
            print(local_path)
            print(remote_path)
            self.sftp_client.put(local_path,
                                 remote_path,
                                 callback=progress_bar)

            self.sftp_client.put('/iapsfile' + one_file['img_path'],
                                 img_path + one_file['img_path'].split('/')[-1],
                                 callback=progress_bar)


    def mode_update(self, note_flag, files_path, hosp_id, mode):
        """
        鉴于一些特殊情况，这个函数用于标注和文件的更新，根据mode来判断更新模型
        Usage:
            >>> mode_update(note_flag=4, files_path='', hosp_id=13,mode=2)
            此时，在所有标号为13的医院数据中，更新所有note_flag为4的xml文件到远程服务器的xml_path路径下
            其中mode=0表示只传标注，1：只传文件，2：都传
        """
        mode_dict = {0:'markfile_path',
                     1:'img_path',
                     2:''}
        if not mode_dict[mode]:
            print('Mode 2 is not currently supported!')
            return False
        if self.client_state == 0:
            self.connect()
        if not self.sftp_client:
            self.sftp_client = paramiko.SFTPClient.from_transport(self.client.get_transport())
            mysql = MysqlDeal(config_yaml=self.config_path, info_yaml=self.info_path)
            new_db = mysql.check_update(i=note_flag)

            particular_list = []
            # particular_list = particular_list.append(i for i in new_db if i['org_id'] is 13)
            for con in new_db:
                if con['org_id'] is hosp_id:
                    particular_list.append(con)
                    # print(con['viscera'])  # 查看标注对应的脏器
            self.total_count = len(particular_list)
            print("Num of files: {}".format(self.total_count))
            print(particular_list)

            # 建立一个表示上传状态的字典,用于失败重传
            # {0:’123‘,1:'23'...}
            succeed_dict = {}
            fail_dict = {}

            file_suffix = {0:'.xml',1:'.tif'}

            for id, con in tqdm(enumerate(particular_list), total=len(particular_list)):
                if self.path_exist(files_path + con['img_file_name'].split('.')[0] + file_suffix[mode]):
                    continue
                print('New file:{}'.format(con['img_file_name'].split('.')[0]))
                try:
                    self.sftp_client.put('/iapsfile' + con[mode_dict[mode]],
                                         files_path + con['img_file_name'].split('.')[0] + file_suffix[mode])
                                         # callback=progress_bar)
                    succeed_dict[id] = con['img_id']

                except Exception as e:
                    print(e)
                    fail_dict[id] = con['img_id']

            if fail_dict:
                print('Failed to upload: {}'.format(fail_dict))
            else:
                print('All succeed to upload! Num:{}'.format(self.total_count))



if __name__ == '__main__':
    client = ParamikoClient(cf_file='./config.yaml',
                            info_file='./info.yaml',
                            log_file='./log.yaml',
                            root_path='/home/lr/zhaiyupeng/fuzhou/')
    # client.get_sync(i=4)
    # client.one_item(i=4,
    #                 # img_path='/data/images/pathology/temp/TianjingTest/images/new/',
    #                 # xml_path='/data/images/pathology/temp/TianjingTest/images/new/')

    # client.annotation_update(note_flag=4,
    #                          xml_path='/data/images/pathology/temp/TjAnnotation/',
    #                          hosp_id=13)
    # TjTiff
    client.mode_update(note_flag=4,
                       files_path='/data/images/pathology/temp/TjTiff/',
                       hosp_id=13,
                       mode=1)