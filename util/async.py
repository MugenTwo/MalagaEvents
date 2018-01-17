# -*- coding: utf-8 -*-
"""
Allows you to make some functions to run in parallel using @async_call decorator and wait_task() function.
https://stackoverflow.com/questions/2632520/what-is-the-fastest-way-to-send-100-000-http-requests-in-python
"""
from threading import Thread
from Queue import Queue


class ParallelTasks(object):
    queue = None

    @staticmethod
    def do_work():
        """ Does some work """
        while True:
            func, args = ParallelTasks.queue.get()
            func(*args)
            ParallelTasks.queue.task_done()

    @staticmethod
    def end_work():
        if ParallelTasks.queue:
            ParallelTasks.queue.join()
            ParallelTasks.queue = None

    @staticmethod
    def start_work(threads=10):
        if not ParallelTasks.queue:
            ParallelTasks.queue = Queue()
            for _ in range(threads):
                thread = Thread(target=ParallelTasks.do_work)
                thread.daemon = True
                thread.start()


def async_call(func):
    """ Decorator that makes a function to be run in parallel when called """
    ParallelTasks.start_work()

    def call(*args):
        ParallelTasks.queue.put((func, args))
    return call


def wait_tasks():
    """ Waits until all current tasks are completed """
    if ParallelTasks.queue:
        ParallelTasks.queue.join()
