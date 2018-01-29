import httplib
import json
import sys
import json
import re
from pprint import pprint
import request_provider





class StaticEntryPusher(object):
    def __init__(self, server):
        self.server = server
    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])
    def set(self, data):
        ret = self.rest_call(data, 'POST')
        return ret[0] == 200
    def remove(self, objtype, data):
        ret = self.rest_call(data, 'DELETE')
        return ret[0] == 200
    def rest_call(self, data, action):
        path = '/wm/staticflowpusher/json'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret



class Switch(StaticEntryPusher):
    def __init__(self, ppid, *argv ):
        self.ppid = ppid
        self.ports = []
        self.stats = ''
        self.flows = {}
        for port in argv:
            self.ports.append(port)

    def flow_maker(self, src_port, dst_port,):
        flow = {}
        flow['switch'] = self.ppid
        flow['name'] = "flow_" + self.ppid[4:] + "_from_" + str(src_port) + "_to_" + str(dst_port)
        flow['priority'] = "636"
        flow['in_port'] = str(src_port)
        flow['actions'] = "output=" + str(dst_port)
        flow['active'] = "true"
        return json.dumps(flow)



def select_route(s1_stats, s2_stats, s3_stats):

    stats =[]
    stats.append(int(s1_stats))
    stats.append(int(s2_stats))
    stats.append(int(s3_stats))
    print "!!!!!", stats
    free_route = min(stats)
    print "free_route ", free_route

    for i in  xrange(3):
        if stats[i] == free_route:
            free_route = i      #numeracja od zera
            print stats[i], "nr ", i+1

    return free_route






def main():
    server = 'http://127.0.0.1:8080'
    postUrl = '/wm/staticflowpusher/json'
    # getSwitchesData = '/wm/core/switch/all/port/json'


    #stworzyc switche
    s1 = Switch("00:00:00:00:00:00:00:01",1,2,3,4)
    s2 = Switch("00:00:00:00:00:00:00:02",1,2,3)
    s3 = Switch("00:00:00:00:00:00:00:03",1,2,3,4)
    s4 = Switch("00:00:00:00:00:00:00:04",1,2,3)
    s5 = Switch("00:00:00:00:00:00:00:05",1,2,3,4)
    #zebrac dla nich statystyki
    REST_api =  request_provider.StaticFlowPusher(server)



    print '/wm/statistics/bandwidth/'+s1.ppid+'/1/json'
    body1 = '/wm/statistics/bandwidth/'+s1.ppid+'/1/json'
    body2 = '/wm/statistics/bandwidth/'+s2.ppid+'/1/json'
    body3 = '/wm/statistics/bandwidth/'+s3.ppid+'/1/json'
    s2.stats = REST_api.get(body1)[0]['bits-per-second-rx']
    s3.stats = REST_api.get(body2)[0]['bits-per-second-rx']
    s4.stats = REST_api.get(body3)[0]['bits-per-second-rx']

    print "LOG\n", s2.stats, "\n", s3.stats, "\n", s4.stats


    #funkcja wybierajaca ktorym switche pojdzie ruch
    free_route = select_route(s2.stats,s3.stats,s4.stats)

    #stworzys flowy
    # instalujemy flow-y
    print "free_route", free_route
    flows_table = []
    if free_route == 1:
        print "idziemy gora"
        print "instalijemy sciezke przez ", s2.ppid
        #sciezka 1
        flows_table.append(s1.flow_maker(1,2))
        flows_table.append(s2.flow_maker(1,3))
        flows_table.append(s5.flow_maker(1,4))
    elif free_route == 2:
        print "idziemy srodkiem"
        print "instalijemy sciezke przez ", s3.ppid
        #sciezka 2
        flows_table.append(s1.flow_maker(1,3))
        flows_table.append(s3.flow_maker(1,3))
        flows_table.append(s5.flow_maker(2,4))
    elif free_route == 3:
        #sciezka 3
        flows_table.append(s1.flow_maker(1,4))
        flows_table.append(s4.flow_maker(1,3))
        flows_table.append(s5.flow_maker(3,4))
        print "idziemy dolem"
        print "instalijemy sciezke przez ", s4.ppid


    # dodac usuwanie flow
    for flow in flows_table:
        print flow
        set_output = REST_api.set(postUrl, flow)
        print set_output



    #(opcjonalnie ktory w petelke co 15 sec)







    # REST_api.set(flow1)





if __name__ == '__main__':
    main()
