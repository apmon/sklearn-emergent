from pprint import pprint
import inspect
import socket; socket.setdefaulttimeout(.1) # TODO: may want to tune this
import json
import numpy
from time import sleep

import sklearn
from sklearn.utils.estimator_checks import check_estimator
from sklearn.base import BaseEstimator, RegressorMixin

# http://stackoverflow.com/questions/23866833/whats-the-full-specification-for-implementing-a-custom-scikit-learn-estimator

# Full instructions are available in the scikit-learn docs, and the
# principles behind the API are set out in this paper by yours truly
# et al. In short, besides fit, what you need for an estimator are
# get_params and set_params that return (as a dict) and set (from
# kwargs) the hyperparameters of the estimator, i.e. the parameters of
# the learning algorithm itself (as opposed to the data parameters it
# learns). These parameters should match the __init__ parameters.

class Transport:
    def __init__(self, address = '127.0.0.1', port = 5360, buffer_size = 1024):
        self.buf_size = buffer_size
        self.address='127.0.0.1'
        self.port=5360

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.address, self.port))

    def __del__(self):
        self.s.close()

    def flush(self):
        while True:
            data = self.s.recv(self.buf_size)
            if not data: break

    def read_json(self):
        total_data=[]
        while True:
            data = self.s.recv(self.buf_size)
            if not data: break
            total_data.append(data)
        return ''.join(total_data)

    def send_json(self, obj):
        self.s.send(json.dumps(obj)+'\n')



class EmergentSklearnRegressor(BaseEstimator, RegressorMixin):

    # All estimators should specify all the parameters that can be set
    # at the class level in their ``__init__`` as explicit keyword
    # arguments (no ``*args`` or ``**kwargs``).
    
    # TODO: set the lrate
    def __init__(self, transport, lrate=.1):

        self.lrate = lrate
        self.transport = transport

        # args, _, _, values = inspect.getargvalues(inspect.currentframe())
        # values.pop("self")
        # for arg, val in values.items():
        #     setattr(self, arg, val)
        #     print("{} = {}".format(arg,val)
        
        self.banner = self.transport.read_json()
        print "banner", self.banner

    def set_member(self, path, member, value):
        try:
            self.transport.send_json({"command": "SetMember", "path": path, "member": member, "var_value": value})
        except Exception, e:
            print str(e)
            return False
        else:
            self.transport.flush()
            return True

    def run_program(self, prog_name):
        try:
            self.transport.send_json({"command": "RunProgram", "program": prog_name})
        except Exception, e:
            print str(e)
            return False
        else:
            self.transport.flush()
            return True
    
    # All logic behind estimator parameters, like translating string
    # arguments into functions, should be done in fit

    def fit(self, X, y):
        self.set_member(".networks.layers.Input.un_geom", "x", X.shape[1])
        self.set_member(".networks.layers.Input.un_geom", "y", 1)
        self.set_member(".networks.layers.Output.un_geom", "x", 1)
        self.set_member(".networks.layers.Output.un_geom", "y", 1)
        self.run_program("SklearnConfigNet")
        
        return self

    def predict(self, X):

        print "Predicting"
        return numpy.full((len(X[:,1]), 1), 1)


emer_sklearn = EmergentSklearnRegressor(transport=Transport())
emer_sklearn.fit(numpy.ones((5,5)), numpy.ones((5,1)))
# result = emer_sklearn.predict(X_test)
del emer_sklearn

# check_estimator(EmergentSklearnRegressor)
