from fdfs_client.client import Fdfs_client, get_tracker_conf

tracker_path = get_tracker_conf('./client.conf')
client = Fdfs_client(tracker_path)
ret = client.upload_by_filename('D:\\work\\pycharm\\doc_parsing\\doc\\pdf\\pdf2.pdf')

# 47.105.141.102:8889/group1/M00/00/00/rB8S22DC1e6ACRu8AHE6ox1uvOg313.pdf
print('47.105.141.102:8889/'+ ret['Remote file_id'].decode())

# docker run -dti  --network=host --name storage -e TRACKER_SERVER=47.105.141.102:22122 -v /var/fdfs/storage:/var/fdfs  -v /etc/localtime:/etc/localtime  delron/fastdfs storage

