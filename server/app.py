import queue
import sys
import time
import logging

from server.tasks.checkForWebRequestTask import CheckForWebRequest
import server.web.server
from server.tasks.openInverterTask import OpenInverterTask
from server.inverters.InverterTCP import InverterTCP

from server.bootstrap import Bootstrap
from server.wifi.scan import WifiScanner

from server.blackboard import BlackBoard

logger = logging.getLogger(__name__)


def main_loop(tasks: queue.PriorityQueue, bb: BlackBoard):
    # here we could keep track of statistics for different types of tasks
    # and adjust the delay to keep the within a certain range

    def add_task(task):
        if task.time < bb.time_ms():
            dt = bb.time_ms() - task.time
            logger.info(
                "task {} is in the past {} adjusting time".format(type(task), dt)
            )
            task.time = bb.time_ms() + 100
        tasks.put(task)

    while True:
        task = tasks.get()
        delay = (task.time - bb.time_ms()) / 1000
        if delay > 0.01:
            time.sleep(delay)

        try:
            new_task = task.execute(bb.time_ms())
        except Exception as e:
            logger.error("Failed to execute task: %s", e)
            new_task = None

        if new_task is not None:
            try:
                for e in new_task:
                    add_task(e)
            except TypeError:
                add_task(new_task)


def main(
    web_host: tuple[str, int],
    inverter: InverterTCP.Setup | None = None,
    bootstrap_file: str | None = None,
):
    bb = BlackBoard()

    web_server = server.web.server.Server(web_host, bb)
    print("Server started http://%s:%s" % (web_host[0], web_host[1]))

    tasks = queue.PriorityQueue()

    bootstrap = Bootstrap(bootstrap_file)

    bb.inverters.add_listener(bootstrap)

    try:
        s = WifiScanner()
        ssids = s.get_ssids()
        print(f"Scanned SSIDs: {ssids}")
    except Exception as e:
        print(e)

    # put some initial tasks in the queue
    if inverter is not None:
        tasks.put(OpenInverterTask(bb.start_time, bb, InverterTCP(inverter)))

    for task in bootstrap.get_tasks(bb.start_time + 500, bb):
        tasks.put(task)

    tasks.put(CheckForWebRequest(bb.start_time + 1000, bb, web_server))

    try:
        main_loop(tasks, bb)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[0])
        print(e)
    finally:
        for i in bb.inverters.lst:
            i.close()
        web_server.close()
        print("Server stopped.")


# this is for debugging purposes only
if __name__ == "__main__":
    import logging

    logging.basicConfig()
    # handler = logging.StreamHandler(sys.stdout)
    # logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
    # main(('localhost', 5000), ("localhost", 502, "huawei", 1), 'bootstrap.txt')
    main(("localhost", 5000), None, "bootstrap.txt")
