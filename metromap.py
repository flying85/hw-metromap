import os
import urllib.request
from urllib.parse import urljoin
import difflib
import argparse
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

    def __repr__(self):
        return self.name        

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
        self.connecting_stops = set()

    def get(self, path='routes', query_key='type', keys='0,1'):
        '''Submits generic get requests to the API
        
           Arguments:
           path -- main object to be downloaded (e.g., routes, stops)
           query_key -- key for filtering
           keys -- values for filtering

           Returns:
           message -- dictionary constructed from JSON API response
        '''
        
        url_path = [self.url, '%s?filter[%s]=%s' % (path, query_key,
                                                    keys)]        
        url_path = '/'.join(url_path)
        try:
            response = urllib.request.urlopen(url_path)
            message = response.read().decode('utf-8')
        except:
            print('ERROR connecting to API.')
            print('Check your connection or wait if hit limit on API calls')
            sys.exit()
        message = json.loads(message)
        return message

    def get_routes(self, query_key='type', keys='0,1'):
        '''Retrieves subway routes from the API

           Arguments:
           query_key -- key for filtering routes
           keys -- values for filtering routes
        '''
        routes_dic = self.get(path='routes', 
                              query_key=query_key, 
                              keys=keys)
        for route in routes_dic['data']:
            self.routes[route['id']] = Route(rid=route['id'], 
                                             long_name=route['attributes']['long_name'],
                                             short_name=route['attributes']['short_name'])            

    def get_stops(self):
        '''Retrieves subway stops along every downloaded route
        '''
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
    
    def max_stops(self):
        '''Prints route with maximum number of subway stops
        
           Returns:
           (route, nstops) -- route name, maximum number of stops
        '''
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
        for stop in self.stops:
            if len(self.stops[stop].parents) > 1 :
                self.connecting_stops.add(stop)
                for parent in self.stops[stop].parents:
                    other_parents = self.stops[stop].parents - {parent}
                    self.routes[parent].neighbors.update(other_parents)   

    def stop_id_from_name(self, stop_name):
        '''Looks up name of a stop, and provides plausible alternatives if not found
        
        Arguments:
        stop_name -- name of the subway stop to look up
        
        Returns:
        stop_id -- id of the stop
        '''
        try:
            stop_id = self.stops_by_name[stop_name]
            return stop_id
        except:
            # Stop name is not in dictionary
            # Propose closest key and exit
            print('\nERROR:'+ stop_name + ' does not correspond to any of the stop names on record.') 
            closest_names = difflib.get_close_matches(stop_name, 
                                                      self.stops_by_name.keys(),
                                                      cutoff=0.3)            
            print('Please update the stop name and retry (e.g., use --src_dest_stops)')
            print('Similar names: ' + ', '.join(closest_names))
            sys.exit()
            
                    
   

    def trip_between_stops(self, src, dest):
        '''Finds path between two stops
        
           Arguments:
           src -- name of starting stop
           dest -- name of destination stop

           Returns:
           trip -- list of metro routes from src to dest
        '''
        src_id  = self.stop_id_from_name(src)
        dest_id = self.stop_id_from_name(dest)
        src_routes = self.stops[src_id].parents
        dest_routes = self.stops[dest_id].parents   
        if src_routes.intersection(dest_routes):
            # If stops are on the same line just return it
            trip = [src_routes.intersection(dest_routes).pop()]
            return trip            
        src_route = src_routes.pop()    
        src_routes.add(src_route) 
        dest_route = dest_routes.pop()    
        dest_routes.add(dest_route) 
        visited_routes = {src_route : 0}
        visited_from   = {src_route : None}           
        cur_routes = [src_route] 
        found_dest = False
        i = 1
        while cur_routes and not(found_dest):            
            next_routes = []
            for cur_route in cur_routes:
                if found_dest : break
                for neighbor_route in self.routes[cur_route].neighbors:                    
                    if neighbor_route not in visited_routes:
                        visited_routes[neighbor_route] = i
                        visited_from[neighbor_route] = cur_route
                        next_routes.append(neighbor_route)
                    if neighbor_route == dest_route:
                        found_dest = True
                        break                        
            cur_routes = next_routes
            i += 1
        trip = [dest_route]
        next_route = visited_from[dest_route]
        while next_route:
            trip = [next_route] + trip
            next_route = visited_from[next_route]  
        return trip
                
    def print_routes(self):
        for route in sorted(self.routes):
            print(self.routes[route])

    def print_stops(self):
        for stop in sorted(self.stops):
            print(self.stops[stop])
        
    def print_connecting_stops(self):
        for stop in self.connecting_stops:
            print(self.stops[stop].name + ' --> ' \
                  + ', '.join(self.stops[stop].parents))




if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='\
    Downloads Boston routes and stations. Suggests path\
    between two subway stops.', 
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)     
    parser.add_argument('--api_url', 
                        default='https://api-v3.mbta.com',
                        help='Root URL of API')   

    parser.add_argument('--src_dest_stops', nargs=2, 
                        help='Names of start and end stops',
                        default=['Brookline Village', 
                                 'Sullivan Square'])
    
    parser.add_argument('--print_stops', action='store_true',
                        help='If provided, just prints\
                        all subway stops and their ids')
    
    parser.add_argument('--print_routes', action='store_true',
                        help='If provided, just prints all\
                        subway routes')

    parser.add_argument('--print_connecting_stops', 
                        action='store_true',
                        help='If provided, just prints all\
                        connecting subway stops and their ids')
    
    args = parser.parse_args()
    
    m = Map()
    print("......Downloading from API ... ")
    m.get_routes()    
    m.get_stops()
    print("......Downloading from API ... done")
    if args.print_routes:
        # Print just routes
        m.print_routes()
    elif args.print_stops:
        # Print just stops
        m.print_stops()
    elif args.print_connecting_stops:
        # Print just connecting stops
        m.print_connecting_stops()
    else:
        # Solve all assignments
        print("======================================")
        print("=========QUESTION 1===================")
        print("======================================")
        m.print_routes()
        print("======================================")
        print("=========QUESTION 2a==================")
        print("======================================")
        route, n = m.max_stops()
        print('Route %s has the maximum number of stops: %d' \
              % (route, n)) 
        route, n = m.min_stops()
        print('Route %s has the minimum number of stops: %d' \
              % (route, n)) 
        print("======================================")
        print("=========QUESTION 2b==================")
        print("======================================")
        m.calc_route_adjacency()    
        m.print_connecting_stops()
        print("======================================")
        print("=========QUESTION 3===================")
        print("======================================")
        print("Plan trip between " + ' and '.join(args.src_dest_stops))
        trip = m.trip_between_stops(*args.src_dest_stops)
        print(', '.join(args.src_dest_stops) + ' --> ' \
              + ', '.join(trip))
