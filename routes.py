# coding=utf-8

from mole import route, run, static_file, error,get, post, put, delete, Mole   # 均来自Mole类
from mole.template import template, Jinja2Template
from mole import request
from mole import response
from mole.mole import json_dumps
from mole import redirect
from mole.sessions import get_current_session, authenticator

from config import  media_prefix
import config
import i18n


auth_required = authenticator(login_url='/auth/login')

@route('/%s/:file#.*#'%media_prefix)
def media(file):
    return static_file(file, root='./media')

@route('/db_tree')
@auth_required()
def db_tree():
    from over_view import get_all_trees
    import config
    try:
        cur_server_index = int(request.GET.get('s', '0'))
        cur_db_index = int(request.GET.get('db', '0'))
        cur_scan_cursor = int(request.GET.get('cursor', '0'))
    except:
        cur_server_index = 0
        cur_db_index = 0
        cur_scan_cursor = 0
    key = request.GET.get('k', '*')
    all_trees = get_all_trees(cur_server_index, key, db=cur_db_index, cursor=cur_scan_cursor)
    if type(all_trees)==list:
        next_scan_cursor, count = all_trees.pop()
        all_trees_json = json_dumps(all_trees)
        error_msg = ''
    else:
        next_scan_cursor, count = 0, 0
        all_trees_json = []
        error_msg = all_trees
    m_config = config.base
    return template('db_tree', 
                    all_trees=all_trees_json, 
                    config=m_config, 
                    cur_server_index=cur_server_index,
                    cur_db_index=cur_db_index,
                    cur_scan_cursor=next_scan_cursor, 
                    pre_scan_cursor=cur_scan_cursor,
                    cur_search_key= (key!='*' and key or ''), 
                    count = count,
                    error_msg = error_msg,
                    media_prefix=media_prefix
                    )


@route('/db_view')
@auth_required()
def db_view():
    try:
        cur_server_index = int(request.GET.get('s', 'server0').replace('server',''))
        cur_db_index = int(request.GET.get('db', 'db0').replace('db',''))
    except:
        cur_server_index = 0
        cur_db_index = 0
    key = request.GET.get('k', '*')
    return template("db_view",media_prefix=media_prefix, cur_server_index=cur_server_index, cur_db_index=cur_db_index, keyword=key)

@route('/server_tree')
@auth_required()
def server_tree():
    from over_view import get_db_trees
    all_trees = get_db_trees()
    return template("server_tree",all_trees=json_dumps(all_trees),media_prefix=media_prefix)

@route('/')
@auth_required()
def server_view():
    return template("main",media_prefix=media_prefix)

@route('/overview')
@auth_required()
def overview():
    from over_view import get_redis_info
    return template('overview', redis_info=get_redis_info(), media_prefix=media_prefix)

@route('/view')
@auth_required()
def view():
    from data_view import general_html,title_html
    fullkey = request.GET.get('key', '')
    refmodel = request.GET.get('refmodel',None)
    
    cl,cur_server_index,cur_db_index = get_cl()
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
@auth_required()
def edit():
    from data_change import edit_value
    key = request.GET.get('key', None)
    value = request.GET.get('value', None)
    type = request.GET.get('type', None)
    new = request.GET.get('new', None)
    score = request.GET.get('score', None)
    cl,cur_server_index,cur_db_index = get_cl()
    edit_value(key,value,new,score,type,cl)
    return '<script type=text/javascript> alert("ok");window.location.href=document.referrer</script>'

@route('/add')
@auth_required()
def add():
    from data_change import add_value
    key = request.GET.get('key', None)
    value = request.GET.get('value', None)
    type = request.GET.get('type', None)
    name = request.GET.get('name', None)
    score = request.GET.get('score', None)
    cl,cur_server_index,cur_db_index = get_cl()
    add_value(key,value,name,score,type,cl)
    return '<script type=text/javascript> alert("ok");window.location.href=document.referrer</script>'

def get_cl():
    from config import base
    from redis_api import get_client
    try:
        cur_server_index = int(request.GET.get('s', '0'))
        cur_db_index = int(request.GET.get('db', '0'))
    except:
        cur_server_index = 0
        cur_db_index = 0
    server = base['servers'][cur_server_index]
    cl = get_client(host=server['host'], port=server['port'],db=cur_db_index, password=server.has_key('password') and server['password'] or None)
    return cl,cur_server_index,cur_db_index
    

@route('/delete')
@auth_required()
def delete():
    from data_change import delete_key, delete_value
    key = request.GET.get('key', '')
    value = request.GET.get('value', None)
    type = request.GET.get('type', None)
    cur_scan_cursor = request.GET.get('cursor', None)
    cl,cur_server_index,cur_db_index = get_cl()
    if value:
        delete_value(key,value,type,cl)
    else:
        delete_key(key,cl, cursor=cur_scan_cursor)
        return '<script type=text/javascript> alert("ok")</script>'
    return '<script type=text/javascript> alert("ok");window.location.href=document.referrer</script>'

@route('/ttl')
@auth_required()
def ttl():
    from data_change import change_ttl
    cl,cur_server_index,cur_db_index = get_cl()
    key = request.GET.get('key', None)
    new = request.GET.get('new', None)
    if new:
        change_ttl(key,int(new),cl)
    return '<script type=text/javascript> alert("ok");window.location.href=document.referrer</script>'

@route('/rename')
@auth_required()
def rename():
    from data_change import rename_key
    cl,cur_server_index,cur_db_index = get_cl()
    key = request.GET.get('key', None)
    new = request.GET.get('new', None)
    rename_key(key,new,cl)
    return '<script type=text/javascript> alert("ok");parent.location.reload();</script>'

@route('/export')
def export():
    return 'Still in developme. You can see it in next version.'

@route('/import')
def iimport():
    return 'Still in developme. You can see it in next version.'

@route('/save')
@auth_required()
def save():
    cl,cur_server_index,cur_db_index = get_cl()
    cl.bgsave()
    return '<script type=text/javascript> alert("ok");window.location.href=document.referrer</script>'


@route('/auth/login', method=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.POST.get("username", '')
        password = request.POST.get("password", '')
        if password == config.admin_pwd and username == config.admin_user:
            session = get_current_session()
            session['username'] = username
            return {'code': 0, 'msg': 'OK'}
        else:
            return {'code': -1, 'msg': '用户名或密码错误'}
    else:
        return template('auth/login.html', config=config)


@route('/auth/logout')
def logout():
    session = get_current_session()
    del session['username']
    return redirect(request.params.get('next') or '/')


if __name__  == "__main__":
    run(host=config.host, port=config.port, reloader=config.debug)