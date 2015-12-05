# coding=utf-8
from time import strftime,localtime
import traceback

from config import  media_prefix
from config import base
    
def get_all_trees(cur_server_index=0,key=None, db=0, cursor=0):
    from redis_api import get_all_keys_tree,get_client
    server = base['servers'][cur_server_index]
    
    cl = get_client(host=server['host'], port=server['port'],db=db, password=server.has_key('password') and server['password'] or None )
    try:
        ret = get_all_keys_tree(client=cl,key=key,cursor=cursor)
        return ret
    except Exception,e:
        traceback.print_exc()
        return u'Error to communicate with %s:%s "%s"'%(server['host'],server['port'], e)
    
def get_db_trees():
    from redis_api import get_tmp_client,check_connect
    servers = base['servers']
    me = [{"pId": "0" ,"id": "root","name":"", "open":True}]
    m_index = 0
    for server in servers:
        id = "server%s"%m_index
        status = check_connect(server['host'], server['port'], password=server.has_key('password') and server['password'] or None)
        if status:
            tar = {"pId": "root", "id": id, "count":"", "name":server["name"]}
            client = get_tmp_client(host=server['host'], port=server['port'], password=server.has_key('password') and server['password'] or None)
            info_dict =client.info()
        else:
            tar = {"pId": "root", "id": id, "name": 'ERROR: Could not connect to Redis ('+server['host']+ ':'+ str(server['port'])+')'}
        me.append(tar)
        
        if status:
            for i in range(server["databases"]):
                if info_dict.has_key("db%s"%i):
                    count = info_dict["db%s"%i]['keys']
                    m_tar = {"pId": id, "id": "db%s"%i, "count": count, "name":"db%s <font color='#BFBFBF'>(%s)</font>"%(i, count)}
                    me.append(m_tar)
        m_index+=1
    return me

def get_redis_info():
    from redis_api import check_connect,get_tmp_client
    servers = base['servers']
    outstr = ''
    ct = 0
    for server in servers:
        status = check_connect(server['host'], server['port'], password=server.has_key('password') and server['password'] or None)
        if status:
            client = get_tmp_client(host=server['host'], port=server['port'], password=server.has_key('password') and server['password'] or None)
            info_dict =client.info()
            if not info_dict.has_key("db0"):
                outstr +="Not exist database (db0)"
            else:
                outstr +='''
                <div class="server" style="float:left; margin-left:20px">
                  <h2>%(name)s</h2>
                  <table class="table table-bordered table-striped" style="max-width: 400px"><tbody>
                      <tr><td><div>Redis version:</div></td><td><div>%(redis_version)s</div></td></tr>
                      <tr><td><div>Keys:</div></td><td><div>%(keys)s</div></td></tr>
                      <tr><td><div>Memory used:</div></td><td><div>%(used_memory)s kb</div></td></tr>
                      <tr><td><div>Uptime:</div></td><td><div>%(uptime_in_seconds)s s</div></td></tr>
                      <tr><td><div>Last save:</div></td><td>
                           <div>
                               %(last_save_time)s 
                               <a href="/save?s=%(s_index)s"><img src="/%(media_prefix)s/images/save.png" width="16" height="16" title="Save Now" alt="[S]" class="imgbut"></a>
                               <a href="/export?s=%(s_index)s"><img src="/%(media_prefix)s/images/export.png" width="16" height="16" title="Export" alt="[E]" class="imgbut"></a>
                                <a href="/import?s=%(s_index)s"><img src="/%(media_prefix)s/images/import.png" width="16" height="16" title="Import" alt="[I]" class="imgbut"></a>
                           </div></td></tr></tbody>
                  </table></div>'''%({
                                'name': server['name'],
                                'redis_version': info_dict['redis_version'],
                                'keys': info_dict['db0']['keys'],
                                'used_memory': info_dict['used_memory']/1024,
                                'uptime_in_seconds': info_dict['uptime_in_seconds'],
                                'last_save_time': strftime("%Y-%m-%d %H:%M:%S",localtime( int(  info_dict.has_key('rdb_last_save_time') and info_dict["rdb_last_save_time"] or info_dict.get('last_save_time', '0')  ) )),
                                's_index':ct,
                                'media_prefix':media_prefix
                                })
        else:
            outstr +='ERROR: Could not connect to Redis ('+server['host']+ ':'+ str(server['port'])+')\n'
        ct +=1
    return outstr