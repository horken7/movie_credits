from moviecredits.datacleaning import INPUT as FILE_DIR
from moviecredits.utils import generate
from typing import Set, Dict
from collections import Counter, defaultdict
import itertools
import array
import numpy as np
import pprint


make = generate.Generate(FILE_DIR, stop=100000)
# actors:{movies}
top_actors = make.top_actors()
movie2actors, id2actors, id2movies = make._connection("movie2actors with id2actors")

def convert_to_actor_name(ids: Set):
    return [id2actors.get(id) for id in list(ids)]

def convert_to_movie_name(id):
    """ids: Integer"""
    return id2movies.get(id)

# TODO End goal to be able to see the connections like this. In order to create a adjacency matrix

class Map_Actors:

    def __init__(self, actor2movies: Dict, movie2actors: Dict):
        self.actor2movies = actor2movies
        self.movie2actors = movie2actors
        self._actor2actors = defaultdict(list)
        self.actor2actors()

    def actor2actors(self):
        """
        create a {actor: {colleagues:times worked together}}
        """

        # go through the movies
        for actor, movies in self.actor2movies.items():
            for movie in movies:
                # return cast
                cast = list(self.movie2actors.get(movie))
                self._actor2actors[actor].append(cast)

            # join list of lists
            merged_list = list(itertools.chain.from_iterable(self._actor2actors[actor]))

            # count the actors
            times_worked_together = Counter(merged_list)

            self._actor2actors[actor] = times_worked_together

    def item(self):
        return self._actor2actors.items()

    def __len__(self):
        return len(self._actor2actors)

    def __repr__(self):
        return "<Map_actors actor2actors:%s >" % (self._actor2actors)

    def as_pairs(self):
        # go through the movies
        for _, movies in top_actors.items():
            for movie in movies:

                # convert to names
                print("movieid: {} movie: {}, actorsid: {}, actors: {}".format(movie,
                                                                               convert_to_movie_name(movie),
                                                                               movie2actors.get(movie),
                                                                               convert_to_actor_name(
                                                                                   movie2actors.get(movie))))
                # return actors
                pairs = list(make.pair_actors(movie2actors.get(movie)))
                if pairs:
                    print(pairs)
                else:
                    print("skip, only one actor")

    def example(self):

        # go through the movies
        for _, movies in self.actor2movies.items():
            for movie in movies:

                # convert to names
                print("movieid: {} movie: {}, actorsid: {}, actors: {}".format(movie,
                                                                               convert_to_movie_name(movie),
                                                                               self.movie2actors.get(movie),
                                                                               convert_to_actor_name(
                                                                                   self.movie2actors.get(movie))))

                # return actors
                pairs = list(make.pair_actors(movie2actors.get(movie)))
                if pairs:
                    print(pairs)
                else:
                    print("skip, only one actor")


class Matrix(Map_Actors):

    def __init__(self, top_actors, movie2actors):
        super(Matrix, self).__init__(top_actors, movie2actors)
        self.actors = set()
        self.possible_colleagues = set()

        self._build_list()

        # initialise matrix
        row = len(self.possible_colleagues)
        col = len(self.actors)
        self.matrix = np.zeros((row, col), dtype=np.uint32)
        self._build_matrix()

    def _build_list(self):
        """
        Build an array for the top_actors (selected actors)
        and build an array for all the possible colleagues are linked to the selected actors
        Use a set to remove duplicates then convert into an array
        """

        for actor, colleagues in super(Matrix, self).item():
            self.actors.add(actor)

            for colleague, _ in colleagues.items():
                self.possible_colleagues.add(colleague)

        self.actors = array.array('i', (self.actors))
        self.possible_colleagues = array.array('i', (self.possible_colleagues))

    def _build_matrix(self):
        """
        Build a matrix of (colleagues against actors) with the weights as the elements
        possible colleagues - row
        top actors - col
        weight - count of the number times the top actor and possible colleagues have worked together in a movie

        it[0] - a feature that allows us to write values to the numpy array while iterating through the array.
        """

        # iterate through matrix
        it = np.nditer(self.matrix, flags=['multi_index'], op_flags=['readwrite'])
        while not it.finished:

            # index position
            colleague_index, actor_index = it.multi_index
            actor = self.actors[actor_index]
            possible_colleague = self.possible_colleagues[colleague_index]

            #check if the possible colleague has worked with the top actor
            a = self._actor2actors.get(actor)
            weight = a.get(possible_colleague)

            # Assign the weights
            if weight is not None:
                it[0] = weight
            else:
                # set the weight to 0 when the possible colleague is not associated to actor
                it[0] = 0

            it.iternext()

    @property
    def get_matrix(self):
        return self.matrix

    def example(self):
        for actor, colleagues in super(Matrix, self).item():
             print("actor {} and no. of colleagues {}".format(actor, len(colleagues)))
             for colleague, time_worked_together in colleagues.items():
                 # actor pairs with their corresponding weight.
                 print(actor, colleague, time_worked_together)

def matrix():
    connections = Matrix(top_actors, movie2actors)
    # the location of the values are changing because the list creation are extracted from unordered data structures.
    # the relative values themselves should not change
    return connections.actors, connections.possible_colleagues, connections.get_matrix


