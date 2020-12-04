#!/usr/bin/env python3

# Server will periodically retrieve a list of scrimmages from API_SCRIM_LIST (found in config)
# and attempt to place those scrimmages on the gcloud pub-sub
# Note: possibly out of date, check with backend to make sure they don't place scrims on pub-sub themselves
# Note: how does this server tell the backend that scrims have been queued? Why would scrims not be queued infinitely?


import util
from config import *

import threading, requests
from apscheduler.schedulers.blocking import BlockingScheduler
from queue import Queue

sched = BlockingScheduler()
scrim_queue = Queue()

def worker():
    while True:
        scrim = scrim_queue.get()
        logging.info('Enqueueing scrimmage: {}'.format(scrim))
        result = util.enqueue({
            'type': 'scrimmage',
            'player1': scrim['player1'],
            'player2': scrim['player2']
        })
        if result == None:
            scrim_queue.put(scrim)

@sched.scheduled_job('cron', minute=0)
def matchmake():
    try:
        logging.info('Obtaining scrimmage list')
        auth_token = util.get_api_auth_token()
        response = requests.get(url=API_SCRIM_LIST, headers={
            'Authorization': 'Bearer {}'.format(auth_token)
        })
        response.raise_for_status()
        scrim_list = response.json()["matches"]
        for scrim in scrim_list:
            scrim_queue.put(scrim)
    except Exception as e:
        logging.critical('Could not get scrimmage list', exc_info=e)

if __name__ == '__main__':
    threads = [threading.Thread(target=worker) for i in range(NUM_WORKER_THREADS)]
    for thread in threads:
        thread.start()
    sched.start()
