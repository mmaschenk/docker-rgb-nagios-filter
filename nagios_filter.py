#!/usr/bin/env python

import os
import pika
import sys
import time
import json
import traceback
import queue
import threading
import datetime
import copy
import uuid
import traceback

PENDING = 1
OK = 2 
WARNING = 4
UNKNOWN = 8
CRITICAL = 16
UP = 2
DOWN = 4
UNREACHABLE = 8

mqrabbit_user = os.getenv("MQRABBIT_USER")
mqrabbit_password = os.getenv("MQRABBIT_PASSWORD")
mqrabbit_host = os.getenv("MQRABBIT_HOST")
mqrabbit_vhost = os.getenv("MQRABBIT_VHOST")
mqrabbit_port = os.getenv("MQRABBIT_PORT")
mqrabbit_exchange = os.getenv("MQRABBIT_EXCHANGE")
mqrabbit_destination = os.getenv("MQRABBIT_DESTINATION")

globalstate = {}


def outputstate(queue, condition):
    global globalstate

    print("[R] Outputting state")
    '''for key, val  in globalstate.items():
        print("\t{0} -> {1}".format(key, val['status']))
        lok = val['last_time_ok']
        lok_date = datetime.datetime.strptime(lok, '%Y-%m-%dT%H:%M:%S.%f')
        lu = datetime.datetime.strptime(val['last_update'], '%Y-%m-%dT%H:%M:%S.%f')
        state.append( { })
        print("\tLast time OK: {0}".format(lok))'''
    newstate = copy.deepcopy(globalstate)
    message = {'servicelist': newstate}
    print("[R] ", message)
    queue.put(message)
    with condition:
        condition.notify()
    #print(globalstate)

def outputmeta(queue, condition, okcount, totalcount):
    print("[R] Outputting metadata")
    message = {'meta': { 'ok': okcount, 'total': totalcount } }
    print("[R] ", message)
    queue.put(message)
    with condition:
        condition.notify()

def update(globalstate, key, value):
    try:
        print("[R] update: key = {0}".format(key))
        #print("Comparing {0} and {1}".format(globalstate[key],value))
        is_same = globalstate[key] == value
        print("[R] Is it the same: {0}".format(is_same))
        globalstate[key] = value
        return not is_same
    except KeyError:
        globalstate[key] = value
        return True

def callback(queue, condition, ch, method, properties, body):
    global globalstate
    #print(" [x] Received %r" % body)
    #time.sleep(body.count(b'.'))
    statuslist = json.loads(body)
    time.sleep(0.1)
    print("[R] Done")
    changed = False
    okcount = 0
    for status in statuslist:
        try:
            s = int(status['status'])
            #print(status['status'])
            key = "{0}@{1}".format(status['description'], status['host_name'])
            print("[R] {0} -> {1}".format(key, status['status']))

            if s == OK:
                okcount = okcount + 1
                if key in globalstate:
                    print("[R] Removing key")
                    del globalstate[key]
                    changed = True
            else:
                print("[R] Adding key")
                changed = update(globalstate, key, status) or changed
        except Exception as e:        
            tb = traceback.extract_stack()
            frame = tb[-2]        
            print("[R] Error parsing json: {0}".format(status))
            print("[R] Exception thrown: [{0}: {1}] at {2} of {3}".format(type(e).__name__, e, frame.lineno, frame.filename))
            print("[R] Record ignored")
            raise
    if changed:
        outputstate(queue, condition)
    else:
        print("[R] nothing changed. no output")
    print("[R] moving on")
    totalcount = len(statuslist)

    outputmeta(queue, condition, okcount, totalcount)
        
    ch.basic_ack(delivery_tag = method.delivery_tag)

def readeventsloop(
            queue,
            condition,
            mqrabbit_user=mqrabbit_user,
            mqrabbit_password=mqrabbit_password, 
            mqrabbit_host=mqrabbit_host,
            mqrabbit_vhost=mqrabbit_vhost,
            mqrabbit_port=mqrabbit_port):

    mqrabbit_credentials = pika.PlainCredentials(mqrabbit_user, mqrabbit_password)
    mqparameters = pika.ConnectionParameters(
        host=mqrabbit_host,
        virtual_host=mqrabbit_vhost,
        port=mqrabbit_port,
        credentials=mqrabbit_credentials)
    mqconnection = pika.BlockingConnection(mqparameters)
    channel = mqconnection.channel()
    channel.exchange_declare(exchange=mqrabbit_exchange, exchange_type='fanout')

    queuename = 'nagios_' + str(uuid.uuid1())
    result = channel.queue_declare(queue=queuename, exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=mqrabbit_exchange, queue=queue_name)

    def cb(ch, method, properties, body):
        callback(queue, condition, ch, method, properties, body)


    channel.basic_consume(queue=queue_name, on_message_callback=cb)

    print('[R] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

    

def start_writer(queue, condition,
            mqrabbit_user=mqrabbit_user,
            mqrabbit_password=mqrabbit_password, 
            mqrabbit_host=mqrabbit_host,
            mqrabbit_vhost=mqrabbit_vhost,
            mqrabbit_port=mqrabbit_port):

    mqrabbit_credentials = pika.PlainCredentials(mqrabbit_user, mqrabbit_password)
    mqparameters = pika.ConnectionParameters(
        host=mqrabbit_host,
        virtual_host=mqrabbit_vhost,
        port=mqrabbit_port,
        credentials=mqrabbit_credentials)
    
    mqconnection = pika.BlockingConnection(mqparameters)
    channel = mqconnection.channel()
    condition.acquire()
    curstate = None
    colortable = {
        PENDING: 'ffff00',
        OK: '00ff00',
        WARNING: '00ffff',
        UNKNOWN: '0000ff',
        CRITICAL: 'ff0000',
    }
    while True:
        print("[W] Waiting for queue")    
        c = condition.wait(120)
        print("[W] Running queue [{0}]".format(c))
        queueitem = {}
        while True:
            if not queue.empty():
                queueitem = queue.get()
                print("[W] Read new current state")            
            print("[W] ",queueitem);
            curstate = queueitem.get('servicelist', None)
            curmeta = queueitem.get('meta', None)
            if curstate != None:
                print("[W] Sending state")
                message = []
                for key, val  in curstate.items():
                    try:
                        print("{0} -> [{1}]".format(key, val['status']))
                        lok = datetime.datetime.strptime(val['last_time_ok'], '%Y-%m-%dT%H:%M:%S.%f')
                        lu = datetime.datetime.strptime(val['last_update'], '%Y-%m-%dT%H:%M:%S.%f')
                        print("[W] \tLast time OK: {0}".format(lok))
                        print("[W] \tLast update: {0}".format(lu))
                        delta = lu - lok
                        print("[W] \tDowntime: {0}".format(delta))
                        statuscode = val['status']
                        message.append( {"text": "{0} ({1}) ".format(key, delta),
                                    "color": colortable[statuscode] } )
                    except:
                        pass
                message = { 'list': message, 'type': 'list', 'key': 'nagios'}
                print("[W] Sending: [{0}]".format(message))
                channel.basic_publish(exchange='', routing_key='nagios_queue', 
                                body=json.dumps(message))
            elif curmeta:
                print("[W] Sending meta state")
                if curmeta['ok'] == curmeta['total']:
                    color = '00ff00'
                elif curmeta['total'] - curmeta['ok'] < 5:
                    color = 'ffff00'
                else:
                    color = 'ff0000'
                message = { 'list': [ 
                                { "text": "{0}/{1} OK".format(curmeta['ok'],curmeta['total']), "color": color } ], 'type': 'list', 'key': 'nagiosmeta' }
                print("[W] Message: [{0}]".format(json.dumps(message)))
                channel.basic_publish(exchange='', routing_key=mqrabbit_destination, body=json.dumps(message))
            else:
                print("[W] No state to send...")
                message = { 'list': [ 
                                { "text": "No failed services ", "color": '00ff00' } ], 'type': 'list', 'key': 'nagios' }

            if queue.empty():
                break

def keep_writing(queue, condition,
            mqrabbit_user=mqrabbit_user,
            mqrabbit_password=mqrabbit_password, 
            mqrabbit_host=mqrabbit_host,
            mqrabbit_vhost=mqrabbit_vhost,
            mqrabbit_port=mqrabbit_port):

    while True:
        try:
            start_writer(queue, condition)
        except Exception as e:
            print("[W] Writer ended unexpectedly")
            stack = traceback.format_stack()
            for l in stack:
                for sl in l.split('\n')[:-1]:
                    print("[W] [Exception]: {0}".format(sl))
            print("[W] Restarting writer")            


def main():
    q = queue.Queue()
    writerWaitState = threading.Condition()

    writer_thread = threading.Thread(target=keep_writing, args=(q,writerWaitState))
    writer_thread.start()
    readeventsloop(queue=q,condition=writerWaitState)

if __name__ == "__main__":
    main()
