# coding=utf-8

from mole import route, run, static_file, error,get, post, put, delete, Mole   # 均来自Mole类
from mole.template import template, Jinja2Template
from mole import request
from mole import response
from mole.mole import json_dumps

from config import  media_prefix

@route('/%s/:file#.*#'%media_prefix)
def media(file):
    return static_file(file, root='./media')

@route('/tree')
def db_tree():
    from over_view import get_all_trees
    import config
    try:
        cur_server_index = int(request.GET.get('s', '0'))
        cur_db_index = int(request.GET.get('db', '0'))
    except:
        cur_server_index = 0
        cur_db_index = 0
    key = request.GET.get('k', '*')
    all_trees = get_all_trees(cur_server_index, key, db=cur_db_index)
    m_config = config.base
    return template('db_tree', all_trees=json_dumps(all_trees), config=m_config, cur_server_index=cur_server_index,cur_db_index=cur_db_index, media_prefix=media_prefix)


@route('/db_view')
def db_view():
    try:
        cur_server_index = int(request.GET.get('s', 'server0').replace('server',''))
        cur_db_index = int(request.GET.get('db', 'db0').replace('db',''))
    except:
        cur_server_index = 0
        cur_db_index = 0
    key = request.GET.get('k', '*')
    return template("db_view",media_prefix=media_prefix, cur_server_index=cur_server_index, cur_db_index=cur_db_index, keyword=key)

@route('/server_view')
def server_tree():
    from over_view import get_db_trees
    all_trees = get_db_trees()
    return template("server_tree",all_trees=json_dumps(all_trees),media_prefix=media_prefix)

@route('/')
def server_view():
    return template("main",media_prefix=media_prefix)

@route('/overview')
def overview():
    from over_view import get_redis_info
    return template('overview', redis_info=get_redis_info(), media_prefix=media_prefix)

@route('/view')
def view():
    from config import base
    from redis_api import get_client
    from data_view import general_html,title_html
    try:
        cur_server_index = int(request.GET.get('s', '0'))
        cur_db_index = int(request.GET.get('db', '0'))
    except:
        cur_server_index = 0
        cur_db_index = 0
    fullkey = request.GET.get('key', '')
    refmodel = request.GET.get('refmodel',None)
    server = base['servers'][cur_server_index]
    cl = get_client(host=server['host'], port=server['port'],db=cur_db_index, password=server.has_key('password') and server['password'] or None)
    if cl.exists(fullkey):
        title_html = title_html(fullkey, cur_server_index, cur_db_index)
        general_html = general_html(fullkey, cur_server_index, cur_db_index, cl)
        out_html = title_html + general_html
        if refmodel:
            return out_html
        else:
            return template('view', out_html=out_html, media_prefix=media_prefix)
    else:
        return '  This key does not exist.'
    
@route('/edit')
def edit():
    return 'Still in developme. You can see it in next version.'

@route('/delete')
def delete():
    from config import base
    from redis_api import get_client
    from data_change import delete_key, delete_value
    try:
        cur_server_index = int(request.GET.get('s', '0'))
        cur_db_index = int(request.GET.get('db', '0'))
    except:
        cur_server_index = 0
        cur_db_index = 0
    key = request.GET.get('key', None)
    value = request.GET.get('value', None)
    type = request.GET.get('type', None)
    server = base['servers'][cur_server_index]
    cl = get_client(host=server['host'], port=server['port'],db=cur_db_index, password=server.has_key('password') and server['password'] or None)
    if value:
        delete_value(key,value,type,cl)
    else:
        delete_key(key,cl)
    return 'ok'

@route('/ttl')
def ttl():
    return 'Still in developme. You can see it in next version.'

@route('/rename')
def rename():
    return 'Still in developme. You can see it in next version.'

@route('/export')
def export():
    return 'Still in developme. You can see it in next version.'

@route('/import')
def iimport():
    return 'Still in developme. You can see it in next version.'

@route('/save')
def info():
    return 'Still in developme. You can see it in next version.'


if __name__  == "__main__":
    run(host='0.0.0.0', port=8086, reloader=True)