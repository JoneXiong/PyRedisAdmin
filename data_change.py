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
        
def rename_key(key,new,cl):
    cl.rename(key,new)
    
def edit_value(key,value,new,score,type,cl):
    if type=="hash":
        cl.hset(key,value,new)
    elif type=="list":
        cl.lset(key, value, new)
    elif type=="set":
        cl.srem(key, value)
        cl.sadd(key, new)
    elif type=="zset":
        cl.zrem(key, value)
        cl.zadd(key,new,float(score) )
    elif type=="string":
        cl.set(key, new)
        
def add_value(key,value,name,score,type,cl):
    if type=="hash":
        cl.hset(key,name,value)
    elif type=="list":
        cl.rpush(key, value)
    elif type=="set":
        cl.sadd(key, value)
    elif type=="zset":
        cl.zadd(key,value,float(score) )
        
def change_ttl(key,new,cl):
    cl.expire(key,new)