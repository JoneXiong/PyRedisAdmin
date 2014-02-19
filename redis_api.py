# coding=utf-8
import redis

import config

client = None
server_ip = None
db_index = None

def connect(*args, **kwargs):
    """ 连接Redis数据库，参数和redis-py的Redis类一样 """
    global client
    client = redis.Redis(*args, **kwargs)

def get_client(*args, **kwargs):
    global server_ip
    global db_index
    if args or kwargs:
        if server_ip!=None and db_index!=None:
            if kwargs['host']==server_ip and kwargs['db']==db_index:
                pass
            else:
                print 'switch conn...'
                connect(*args, **kwargs)
                server_ip = kwargs['host']
                db_index = kwargs['db']
        else:
            print 'init conn...'
            connect(*args, **kwargs)
            server_ip = kwargs['host']
            db_index = kwargs['db']
            
    global client
    if client:
        return client
    else:
        connect(host='127.0.0.1', port=6379)
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
        key_levels = key.split(config.base['seperator'])
        cur = me
        for lev in key_levels:
            if cur.has_key(lev):
                if cur.keys()==0:
                    cur[lev] = {lev:{}}#append(lev)
            else:
                cur[lev] = {}
            cur = cur[lev]
    return me

def get_all_keys_tree(client=None,key='*'):
    if key!='*':
        key = '*%s*'%key
    if client:
        m_all = client.keys(key)
    else:
        m_all = get_client().keys(key)
    m_all.sort()
    me = {'root':{"pId": "0" ,"id": "root","name":"","count":0, "open":True}}
    for key in m_all:
        if len(key)>100:
            continue
        key_levels = key.split(config.base['seperator'])
        pre = 'root'
        for lev in key_levels:
            id = (pre!='root' and '%s%s%s'%(pre,config.base['seperator'],lev) or lev)
            if me.has_key(id):
                pre = id
            else:
                tar = {"pId": pre,"id": id,"name":lev,"count":0}
                me[id] = tar
                me[pre]["count"]+= 1
                pre = id
    ret = me.values()
    for e in ret:
        child_len = e['count']
        fullkey = e['id']
        if child_len==0:
            m_type = client.type(fullkey)
            if not m_type:return
            m_len = 0
            if m_type=='hash':
                m_len = client.hlen(fullkey)
            elif m_type=='list':
                m_len = client.llen(fullkey)
            elif m_type=='set':
                m_len = len(client.smembers(fullkey))
            elif m_type=='zset':
                m_len = len(client.zrange(fullkey,0,-1))
        else:
            m_len = child_len
        e['name'] = "%s <font color='#BFBFBF'>(%s)</font>"%(e['name'],m_len)
    return me.values()
    
def check_connect(host,port, password=None):
    from redis import Connection
    try:
        conn = Connection(host=host, port=port, password=password)
        conn.connect()
        return True
    except:
        return False
    