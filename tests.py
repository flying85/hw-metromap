import unittest
import metromap

class TestStop(unittest.TestCase):
    def setUp(self):
        self.stop = metromap.Stop('idx', 'test_stop')        

    def test_attributes(self):
        self.assertEqual(self.stop.sid, 'idx')
        self.assertEqual(self.stop.name, 'test_stop')
        self.assertFalse(self.stop.parents)


class TestRoute(unittest.TestCase):
    def setUp(self):
        self.route = metromap.Route('idx', 'Long Route', 'Long')

    def test_attributes(self):
        self.assertEqual(self.route.rid, 'idx')
        self.assertEqual(self.route.long_name, 'Long Route')
        self.assertEqual(self.route.short_name, 'Long')
        self.assertFalse(self.route.stops)
        self.assertEqual(self.route.nstops, 0)
        self.assertFalse(self.route.neighbors)
        
    def test_print(self):
        self.assertEqual(repr(self.route), 'Long Route')

class TestMap(unittest.TestCase):

    def setUp(self):
        self.m = metromap.Map()

    def test_attributes(self):
        self.assertEqual(self.m.url, 'https://api-v3.mbta.com')
        self.assertFalse(self.m.routes)
        self.assertFalse(self.m.stops)
        self.assertFalse(self.m.stops_by_name)
    
    def test_get(self):
        dd = self.m.get(path='routes', query_key='id', keys='Red,Green-B')
        self.assertEqual(len(dd['data']), 2)

    def test_get_routes(self):
        self.m.get_routes(query_key='id', keys='Red,Green-B')
        self.assertIn('Red', self.m.routes)
        self.assertIn('Green-B', self.m.routes)        

    def test_get_stops(self):
        self.m.get_routes(query_key='id', keys='Red,Green-B')
        self.m.get_stops()
        self.assertIn('place-knncl', self.m.stops)
        self.assertIn('place-knncl', self.m.routes['Red'].stops)
        self.assertIn('place-harvd', self.m.stops)        
        self.assertIn('place-harvd', self.m.routes['Green-B'].stops)        
    def test_max_min_stops(self):
        self.m.get_routes(query_key='id', keys='Red,Green-B')
        self.m.get_stops()
        self.assertEqual(self.m.max_stops()[0], 'Green-B')
        self.assertEqual(self.m.min_stops()[0], 'Red')

    def test_adjacency(self):
        self.m.get_routes(query_key='id', keys='Red,Green-B')
        self.m.get_stops()
        self.m.calc_route_adjacency()
        self.assertIn('Red', self.m.routes['Green-B'].neighbors)
        self.assertIn('Green-B', self.m.routes['Red'].neighbors)

    def test_trip(self):
        self.m.get_routes(query_key='id', keys='Red,Green-B')
        self.m.get_stops()
        self.m.calc_route_adjacency()
        trip = self.m.trip_between_stops('Kendall/MIT', 
                                         'Harvard Avenue')
        self.assertEqual(trip, ['Red', 'Green-B'])
        trip = self.m.trip_between_stops('Harvard Avenue',
                                         'Kendall/MIT')
        self.assertEqual(trip, ['Green-B', 'Red'])


if __name__ == '__main__':
    unittest.main()
     
