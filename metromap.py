import os
import urllib.request
from urllib.parse import urljoin
import json
import sys

class Stop:
    '''Class to describe subway stops

       Stop.parents -- set of routes intersecting at the stop
    
       Arguments:
       sid -- subway stop id
       name -- subway stop name
    '''
    def __init__(self, sid, name):
        self.sid = sid
        self.name = name
        self.parents = set()
        

class Route:
    '''Class to describe subway routes.

       Route.stops -- dictionary of subway stops along route 
    
       Arguments: 
       rid -- route id
       long_name -- long name of the route
       short_name -- short name of the route
    '''
    
    def __init__(self, rid, long_name, short_name):
        
        self.rid = rid
        self.long_name = long_name
        self.short_name = short_name
        self.stops = set()
        self.nstops = 0
        self.neighbors = set()

    def __repr__(self):
        return self.long_name
        
class Map:
    '''Retrieves subway routes and stops 

       Map.routes -- dictionary of all subway routes
       Map.stops -- dictionary of all subway stops
       Map.stops_by_name -- dictionary mapping stop names to stop ids

       Arguments:
       url -- root API url to retrieve subway routes and stops 
    '''

    def __init__(self, url='https://api-v3.mbta.com'):
        self.url = url
        self.routes = {}
        self.stops = {}
        self.stops_by_name = {}
        self.routes_downloaded = False
        self.stops_downloaded  = False

    def get(self, path='routes', query_key='type', keys='0,1'):
        '''Submits generic get requests to the API
        
           Arguments:
           path -- main object to be downloaded (e.g., routes, stops)
           query_key -- key for filtering
           keys -- values for filtering

           Returns:
           message -- dictionary constructed from JSON API response
        '''

        url_path = [self.url, '%s?filter[%s]=%s' % (path, query_key, keys)]
        url_path = '/'.join(url_path)
        response = urllib.request.urlopen(url_path)
        message = response.read().decode('utf-8')
        message = json.loads(message)
        return message

    def get_routes(self, overwrite=False, query_key='type', keys='0,1'):
        '''Retrieves subway routes from the API

           Arguments:
           overwrite -- flag to overwrite routes even if already
                        downloaded
           query_key -- key for filtering routes
           keys -- values for filtering routes
        '''
        if overwrite or not self.routes_downloaded:
            self.routes = {}
            routes_dic = self.get(path='routes', 
                                  query_key=query_key, 
                                  keys=keys)
            for route in routes_dic['data']:
                self.routes[route['id']] = Route(rid=route['id'], 
                                                 long_name=route['attributes']['long_name'],
                                                 short_name=route['attributes']['short_name'])
            self.routes_downloaded = True
            self.stops_downloaded  = False

    def get_stops(self, overwrite=False):
        '''Retrieves subway stops from the API

           Arguments:
           overwrite -- flag to overwrite routes even if already downloaded
        '''
        if overwrite or not self.stops_downloaded:
            for route in self.routes:
                route_stops = self.get(path='stops', query_key='route', keys=route)
                for route_stop in route_stops['data']:
                    if route_stop['id'] not in self.stops:                        
                        stop_name = route_stop['attributes']['name']
                        self.stops[route_stop['id']] = Stop(sid=route_stop['id'],
                                                            name=stop_name)
                        self.stops_by_name[stop_name] = route_stop['id']
                    self.stops[route_stop['id']].parents.add(route)
                    self.routes[route].stops.add(route_stop['id'])
                    self.routes[route].nstops += 1

            self.stops_downloaded = True

    
    def max_stops(self):
        '''Prints route with maximum number of subway stops
        
           Returns:
           (route, nstops) -- route name, maximum number of stops
        '''
        self.get_routes()
        self.get_stops()
        max_stop_route = ''
        max_nstops = -1
        for route in self.routes:
            if self.routes[route].nstops > max_nstops:                
                max_nstops = self.routes[route].nstops
                max_nstops_route = route

        return (max_nstops_route, max_nstops)
        
    def min_stops(self):
        '''Finds route with minimum number of subway stops

           Returns:
           (route, nstops) -- route name, maximum number of stops
        '''
        self.get_routes()
        self.get_stops()
        min_stop_route = ''
        min_nstops = sys.maxsize
        for route in self.routes:
            if  self.routes[route].nstops < min_nstops:
                min_nstops = self.routes[route].nstops
                min_nstops_route = route

        return (min_nstops_route, min_nstops)

    def calc_route_adjacency(self):
        '''Computes adjacency between routes and updates Route.neighbors and Stop.parents
        '''
        self.get_routes()
        self.get_stops()
        for stop in self.stops:
            if len(self.stops[stop].parents) > 1 :
                for parent in self.stops[stop].parents:
                    other_parents = self.stops[stop].parents - {parent}
                    self.routes[parent].neighbors.update(other_parents)            
   

    def trip_between_stops(self, src, dest):
        '''Finds path between two stops
        
           Arguments:
           src -- name of starting stop
           dest -- name of destination stop

           Returns:
           trip -- list of metro routes from src to dest
        '''
        src_id  = self.stops_by_name[src]
        dest_id = self.stops_by_name[dest]
        src_routes = self.stops[src_id].parents
        dest_routes = self.stops[dest_id].parents        
        src_route = src_routes.pop()    
        src_routes.add(src_route) 
        dest_route = dest_routes.pop()    
        dest_routes.add(dest_route) 
        visited_routes = {src_route : 0}
        visited_from   = {src_route : None}           
        cur_routes = [src_route] 
        i = 1
        while cur_routes:            
            next_routes = []
            for cur_route in cur_routes:
                for neighbor_route in self.routes[cur_route].neighbors:                    
                    if neighbor_route not in visited_routes:
                        visited_routes[neighbor_route] = i
                        visited_from[neighbor_route] = cur_route
                        next_routes.append(neighbor_route)
            cur_routes = next_routes
            i += 1

        trip = [dest_route]
        next_route = visited_from[dest_route]
        while next_route:
            trip = [next_route] + trip
            next_route = visited_from[next_route]  
        return trip
                
    def print_routes(self):
        self.get_routes()
        for route in self.routes:
            print(self.routes[route])
        
    def print_connecting_stops(self):
        self.get_routes()
        self.get_stops()
        for stop in self.stops:
            if len(self.stops[stop].parents) > 1:
                print(self.stops[stop].name + ' --> ' + ', '.join(self.stops[stop].parents))


if __name__ == '__main__':

    m = Map()
    routes = m.get_routes()
    print("======================================")
    print("=========QUESTION 1===================")
    print("======================================")
    m.print_routes()
    print("======================================")
    print("=========QUESTION 2a==================")
    print("======================================")
    route, n = m.max_stops()
    print('Route %s has the maximum number of stops: %d' % (route, n)) 
    route, n = m.min_stops()
    print('Route %s has the minimum number of stops: %d' % (route, n)) 
    print("======================================")
    print("=========QUESTION 2b==================")
    print("======================================")
    m.print_connecting_stops()
    m.calc_route_adjacency()
    print("======================================")
    print("=========QUESTION 3===================")
    print("======================================")
    trip = m.trip_between_stops('Brookline Village', 
                                'Sullivan Square')
    print('Brookline Village, Sullivan Square --> ' + ', '.join(trip))
