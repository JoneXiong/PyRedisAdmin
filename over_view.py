# coding=utf-8
from time import strftime,localtime

def print_namespace(node, name, fullkey, islast,client, sid):
    cl = client
    sb = ''
    
    child_len = len(node.keys())
    if child_len==0:
        m_type = cl.type(fullkey)
        if not m_type:return
        
        m_len = 0
        if m_type=='hash':
            m_len = cl.hlen(fullkey)
        elif m_type=='list':
            m_len = cl.llen(fullkey)
        elif m_type=='set':
            m_len = len(cl.smembers(fullkey))
        elif m_type=='zset':
            m_len = len(cl.zrange(fullkey,0,-1))
        
        m_class = []
#        if fullkey == GET['key']:
#            m_class.append('current')
        if islast:
            m_class.append('last')
        
        m_span = ''
        if m_len:
            m_span = '<span class="info">(%s)</span>'%m_len
        
        sb += '<li class="%s"><a href="/view?s=%s&amp;key=%s">%s %s</a></li>'%( ' '.join(m_class), sid, fullkey, name,  m_span)

    else:
        sb += '<li class="folder %s %s"><div class="icon">%s <span class="info">(%s)</span></div><ul>'%( (fullkey and 'collapsed' or ''), (islast and 'last' or ''), name, len(node) )
        ct = len(node.keys())
        for childname in node.keys():
            childnode = node[childname]
            if fullkey:
                childfullkey = fullkey+':'+childname
            else:
                childfullkey = childname
            ct = ct - 1
            sb += print_namespace(childnode, childname, childfullkey, ct==0, cl, sid)
        sb += '</ul></li>'
    return sb

def get_all_levels(cur_server_index=0):
    from redis_api import get_all_keys_dict,get_client
    from config import base
    server = base['servers'][cur_server_index]
    cl = get_client(host=server['host'], port=server['port'])
    try:
        namespaces = get_all_keys_dict(client=cl)
        return print_namespace(namespaces, 'Keys', '', bool(namespaces), cl, cur_server_index)
    except:
        return u'Could not connect %s:%s'%(server['host'],server['port'])

def get_redis_info():
    from config import base
    from redis_api import check_connect,get_tmp_client
    servers = base['servers']
    outstr = ''
    ct = 0
    for server in servers:
        status = check_connect(server['host'], server['port'])
        if status:
            client = get_tmp_client(host=server['host'], port=server['port'])
            info_dict =client.info() 
            outstr +='''
            <div class="server">
              <h2>%(name)s</h2>
              <table>
                  <tr><td><div>Redis version:</div></td><td><div>%(redis_version)s</div></td></tr>
                  <tr><td><div>Keys:</div></td><td><div>%(keys)s</div></td></tr>
                  <tr><td><div>Memory used:</div></td><td><div>%(used_memory)s kb</div></td></tr>
                  <tr><td><div>Uptime:</div></td><td><div>%(uptime_in_seconds)s s</div></td></tr>
                  <tr><td><div>Last save:</div></td><td><div>%(last_save_time)s <a href="/save?s=%(s_index)s"><img src="/media/images/save.png" width="16" height="16" title="Save Now" alt="[S]" class="imgbut"></a></div></td></tr>
              </table></div>'''%({
                            'name': server['name'],
                            'redis_version': info_dict['redis_version'],
                            'keys': info_dict['db0']['keys'],
                            'used_memory': info_dict['used_memory']/1024,
                            'uptime_in_seconds': info_dict['uptime_in_seconds'],
                            'last_save_time': strftime("%Y-%m-%d %H:%M:%S",localtime(int(info_dict['last_save_time']))),
                            's_index':ct
                            })
        else:
            outstr +='ERROR: Could not connect to Redis ('+server['host']+ ':'+ str(server['port'])+')\n'
        ct +=1
    return outstr