from remoteSync import ParamikoClient

if __name__ == '__main__':
    client = ParamikoClient(cf_file='./config.yaml',
                            info_file='./info.yaml',
                            log_file='./log.yaml',
                            root_path='/home/lr/zhaiyupeng/fuzhou/')
    client.get_sync(i=4)
