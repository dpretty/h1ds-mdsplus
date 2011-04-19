from celery.decorators import task

@task()
def mds_event_listener(server, event_name):
    import os, MDSplus
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            print self.getName()
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)    

