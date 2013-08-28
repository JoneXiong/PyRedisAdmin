# coding=utf-8

def delete_key(key,cl):
    cl.delete(key)

def delete_value(key,value,type,cl):
    if type=="hash":
        cl.hdel(key, value)
    elif type=="list":
        cl.lset(key, value, '__delete__')
        cl.lrem(key, '__delete__', 0)
    elif type=="set":
        cl.srem(key, value)
    elif type=="zset":
        cl.zrem(key, value)