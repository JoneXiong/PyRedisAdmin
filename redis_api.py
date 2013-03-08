# coding=utf-8
import redis

client = None

def connect(*args, **kwargs):
    """ 连接Redis数据库，参数和redis-py的Redis类一样 """
    global client
    client = redis.Redis(*args, **kwargs)

def get_client(*args, **kwargs):
    if args or kwargs:
        connect(*args, **kwargs)
    global client
    return client

def get_tmp_client(*args, **kwargs):
    from redis import Redis
    return Redis(*args, **kwargs)

def get_all_keys_dict(client=None):
    if client:
        m_all = client.keys()
    else:
        m_all = get_client().keys()
    m_all.sort()
    me = {}
    for key in m_all:
        if len(key)>100:
            continue
        key_levels = key.split(':')
        cur = me
        for lev in key_levels:
            if cur.has_key(lev):
                if cur.keys()==0:
                    cur[lev] = {lev:{}}#append(lev)
            else:
                cur[lev] = {}
            cur = cur[lev]
    return me
    
def check_connect(host,port):
    from redis import Connection
    try:
        conn = Connection(host=host, port=port)
        conn.connect()
        return True
    except:
        return False
    