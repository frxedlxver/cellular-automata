import numpy as np

class NbShape:
    Lonely = np.array([[0, 0]])
    Cross = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])
    Square = np.vstack([Cross, [[1, 1], [1, -1], [-1, 1], [-1, -1]]])
    Diamond = np.vstack([Cross, Square, [2, 0], [-2, 0], [0, 2], [0, -2]])

class Neighbourhood:
    Von = {
        "name" : "Von",
        "shape": NbShape.Cross,
        "range": 1
    }
    Moore = {
        "name" : "Moore",
        "shape": NbShape.Square,
        "range": 1
    }
    ExVon = {
        "name" : "ExVon",
        "shape": NbShape.Cross,
        "range": 2
    }
    ExMoore = {
        "name" : "ExMoore",
        "shape": NbShape.Square,
        "range": 2
    }
    Lonely = {
        "name" : "Lonely",
        "shape": NbShape.Lonely,
        "range": 1
    }

    _neighbourhood_cache = {}
    
    @staticmethod
    def get_neighbourhood(nb):
        # Check if the neighbourhood is already cached
        if nb['name'] in Neighbourhood._neighbourhood_cache:
            return Neighbourhood._neighbourhood_cache[nb]

        shape = nb['shape']
        nb_range = nb['range']

        if nb_range == 1:
            result = shape
        else:
            # Properly scale the neighborhood
            result = Neighbourhood.scale_neighbourhood(shape, nb_range)

        # Cache and return the result
        Neighbourhood._neighbourhood_cache[nb['name']] = result
        return result

    @staticmethod
    def scale_neighbourhood(nb_shape, nb_scale):
        scaled_shape = []
        for offset in nb_shape:
            for r in range(-nb_scale, nb_scale + 1):
                scaled_shape.append([offset[0] + r, offset[1] + r])
        return np.array(scaled_shape)
