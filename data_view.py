# coding=utf-8
'''
数据相关视图
'''

from config import media_prefix


def title_html(fullkey, sid, db):
    out = '''
    <h2>%(fullkey)s
          <a class="btn" href="/rename?s=%(sid)s&db=%(db)s&amp;key=%(fullkey)s" onclick="renameKey(this.href,'%(fullkey)s');return false;" title="Rename"><i class="icon-edit"></i></a>
          <a class="btn" href="/delete?s=%(sid)s&db=%(db)s&amp;key=%(fullkey)s" title="Delete"><i class="icon-remove"></i></a>
          <a class="btn" href="/export?s=%(sid)s&db=%(db)s&amp;key=%(fullkey)s" title="Export"><i class="icon-download-alt"></i></a>
    </h2>''' % ({'sid': sid, 'db': db, 'fullkey': fullkey, 'media_prefix': media_prefix})
    return out


def general_html(fullkey, sid, db, client):
    cl = client
    m_type = cl.type(fullkey)
    m_ttl = cl.ttl(fullkey)
    m_ttl = m_ttl and m_ttl or ''
    redis_version = cl.info()['redis_version']
    if redis_version >= '2.2.3':
        m_encoding = cl.object('encoding', fullkey)
    else:
        m_encoding = ''
    m_len = 0
    m_detail = ''
    m_other = '''<p>
    <a href="/add?s=%(sid)s&db=%(db)s&amp;type=%(type)s&amp;key=%(fullkey)s" onclick="add(this.href,'%(type)s');return false;" class="add">Add another value</a>
    </p>''' % ({'sid': sid, 'db': db, 'type': m_type, 'fullkey': fullkey})

    if m_type == 'string':
        val = cl.get(fullkey)
        m_len = len(val)
        m_detail = string_html(fullkey, sid, db, client)
        m_other = ''
    if m_type == 'hash':
        m_len = cl.hlen(fullkey)
        m_detail = hash_html(fullkey, sid, db, client)
    elif m_type == 'list':
        m_len = cl.llen(fullkey)
        m_detail = list_html(fullkey, sid, db, client)
    elif m_type == 'set':
        m_len = len(cl.smembers(fullkey))
        m_detail = set_html(fullkey, sid, db, client)
    elif m_type == 'zset':
        m_len = len(cl.zrange(fullkey, 0, -1))
        m_detail = zset_html(fullkey, sid, db, client)

    out = '''
    <table class="table table-bordered table-striped" style="max-width: 400px">
        <tr><td><div>Type:</div></td><td><div>%(type)s</div></td></tr>
        <tr><td><div><abbr title="Time To Live">TTL</abbr>:</div></td><td><div>%(ttl)s <a class="btn" href="/ttl?s=%(sid)s&db=%(db)s&amp;key=%(fullkey)s" onclick="changeTTL(this.href,'%(ttl)s');return false;" title="Edit TTL"><i class="icon-edit"></i></a></div></td></tr>
        <tr><td><div>Encoding:</div></td><td><div>%(encoding)s</div></td></tr>
        <tr><td><div>Size:</div></td><td><div>%(size)s</div></td></tr>
    </table>''' % (
    {'type': m_type, 'ttl': m_ttl, 'sid': sid, 'db': db, 'fullkey': fullkey, 'encoding': m_encoding, 'size': m_len,
     'media_prefix': media_prefix})
    return out + m_detail + m_other


def string_html(fullkey, sid, db, client):
    m_value = client.get(fullkey)
    out = '''
    <table class="table table-bordered table-striped">
        <tr><td><div>%(value)s</div></td><td><div>
          <a class="btn" href="/edit?s=%(sid)s&db=%(db)s&amp;type=string&amp;key=%(fullkey)s" onclick="edit(this.href,'%(value)s');return false;" title="Edit"><i class="icon-edit"></i></a>
        </div></td></tr>
    </table>
    ''' % ({'value': m_value, 'sid': sid, 'db': db, 'fullkey': fullkey, 'media_prefix': media_prefix})
    return out


def hash_html(fullkey, sid, db, client):
    out = '''
    <table class="table table-bordered table-striped">
    <tr><th><div>Key</div></th><th><div>Value</div></th><th><div>&nbsp;</div></th><th><div>&nbsp;</div></th></tr>'''
    m_values = client.hgetall(fullkey)
    alt = False
    for key, value in m_values.items():
        if len(value) > 200:
            value = 'data(len:%s)' % len(value)
        alt_str = alt and 'class="alt"' or ''
        out += '''<tr %(alt_str)s><td><div>%(key)s</div></td><td><div>%(value)s</div></td><td><div>
          <a class="btn" href="/edit?s=%(sid)s&db=%(db)s&amp;type=hash&amp;key=%(fullkey)s&amp;value=%(key)s" onclick="edit(this.href,'%(value)s');return false;" title="Edit"><i class="icon-edit"></i></a>
        </div></td><td><div>
          <a class="btn" href="/delete?s=%(sid)s&db=%(db)s&amp;type=hash&amp;key=%(fullkey)s&amp;value=%(key)s" class="delval" title="Delete"><i class="icon-remove"></i></a>
        </div></td></tr>
        ''' % ({'value': value, 'key': key, 'sid': sid, 'db': db, 'fullkey': fullkey, 'alt_str': alt_str,
                'media_prefix': media_prefix})
        alt = not alt
    out += '</table>'
    return out


def list_html(fullkey, sid, db, client):
    out = '''
    <table class="table table-bordered table-striped">
    <tr><th><div>Index</div></th><th><div>Value</div></th><th><div>&nbsp;</div></th><th><div>&nbsp;</div></th></tr>'''
    m_values = client.lrange(fullkey, 0, -1)
    alt = False
    index = 0
    for value in m_values:
        alt_str = alt and 'class="alt"' or ''
        out += '''<tr %(alt_str)s><td><div>%(index)s</div></td><td><div>%(value)s</div></td><td><div>
          <a class="btn" href="/edit?s=%(sid)s&db=%(db)s&amp;type=list&amp;key=%(fullkey)s&amp;value=%(index)s" onclick="edit(this.href,'%(value)s');return false;" title="Edit"><i class="icon-edit"></i></a>
        </div></td><td><div>
          <a class="btn" href="/delete?s=%(sid)s&db=%(db)s&amp;type=list&amp;key=%(fullkey)s&amp;value=%(index)s" class="delval" title="Delete"><i class="icon-remove"></i></a>
        </div></td></tr>
        ''' % ({'value': value.replace('"', '\\\''), 'index': index, 'sid': sid, 'db': db, 'fullkey': fullkey,
                'alt_str': alt_str, 'media_prefix': media_prefix})
        alt = not alt
        index += 1
    out += '</table>'
    return out


def set_html(fullkey, sid, db, client):
    out = '''
    <table class="table table-bordered table-striped">
    <tr><th><div>Value</div></th><th><div>&nbsp;</div></th><th><div>&nbsp;</div></th></tr>'''
    m_values = client.smembers(fullkey)
    alt = False
    for value in m_values:
        alt_str = alt and 'class="alt"' or ''
        out += '''<tr %(alt_str)s><td><div>%(value)s</div></td><td><div>
          <a class="btn" href="/edit?s=%(sid)s&db=%(db)s&amp;type=set&amp;key=%(fullkey)s&amp;value=%(value)s" onclick="edit(this.href,'%(value)s');return false;" title="Edit"><i class="icon-edit"></i></a>
        </div></td><td><div>
          <a class="btn" href="/delete?s=%(sid)s&db=%(db)s&amp;type=set&amp;key=%(fullkey)s&amp;value=%(value)s" class="delval" title="Delete"><i class="icon-remove"></i></a>
        </div></td></tr>
        ''' % (
        {'value': value, 'sid': sid, 'db': db, 'fullkey': fullkey, 'alt_str': alt_str, 'media_prefix': media_prefix})
        alt = not alt
    out += '</table>'
    return out


def zset_html(fullkey, sid, db, client):
    out = '''
    <table class="table table-bordered table-striped">
    <tr><th><div>Score</div></th><th><div>Value</div></th><th><div>&nbsp;</div></th><th><div>&nbsp;</div></th></tr>'''
    m_values = client.zrange(fullkey, 0, -1)
    alt = False
    for value in m_values:
        score = client.zscore(fullkey, value)
        alt_str = alt and 'class="alt"' or ''
        out += '''<tr %(alt_str)s><td><div>%(score)s</div></td><td><div>%(value)s</div></td><td><div>
          <a class="btn" href="/edit?s=%(sid)s&db=%(db)s&amp;type=zset&amp;key=%(fullkey)s&amp;value=%(value)s;score=%(score)s" onclick="edit(this.href,'%(value)s');return false;" title="Edit"><i class="icon-edit"></i></a>
        </div></td><td><div>
          <a class="btn" href="/delete?s=%(sid)s&db=%(db)s&amp;type=zset&amp;key=%(fullkey)s&amp;value=%(value)s" class="delval" title="Delete"><i class="icon-remove"></i></a>
        </div></td></tr>
        ''' % ({'value': value, 'score': score, 'sid': sid, 'db': db, 'fullkey': fullkey, 'alt_str': alt_str,
                'media_prefix': media_prefix})
        alt = not alt
    out += '</table>'
    return out
