# coding=utf-8

from mole import route, run, static_file, error,get, post, put, delete, Mole   # 均来自Mole类
from mole.template import template, Jinja2Template
from mole import request
from mole import response

@route('/media/:file#.*#')
def media(file):
    return static_file(file, root='./media')

@route('/')
def index():
    from over_view import get_all_levels
    import config
    try:
        cur_server_index = int(request.GET.get('s', '0'))
    except:
        cur_server_index = 0
    all_levels_tree = get_all_levels(cur_server_index)
    m_config = config.base
    return template('index', all_levels_tree=all_levels_tree, config=m_config, cur_server_index=cur_server_index)

@route('/overview')
def overview():
    from over_view import get_redis_info
    return template('overview', redis_info=get_redis_info())

@route('/view')
def view():
    from config import base
    from redis_api import get_client
    from data_view import general_html,title_html
    try:
        sid = int(request.GET.get('s', '0'))
    except:
        sid = 0
    fullkey = request.GET.get('key', '')

    server = base['servers'][sid]
    cl = get_client()#get_client(host=server['host'], port=server['port'])
    if cl.exists(fullkey):
        title_html = title_html(fullkey, sid)
        general_html = general_html(fullkey, sid, cl)
        out_html = title_html + general_html
        #return template('view',template_adapter=Jinja2Template, out_html=out_html )
        return template('view', out_html=out_html )
    else:
        return '  This key does not exist.'
    
@route('/edit')
def edit():
    return 'Still in developme. You can see it in next version.'

@route('/delete')
def delete():
    return 'Still in developme. You can see it in next version.'

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

@route('/info')
def info():
    return 'Still in developme. You can see it in next version.'


if __name__  == "__main__":
    run(host='localhost', port=8086, reloader=True)