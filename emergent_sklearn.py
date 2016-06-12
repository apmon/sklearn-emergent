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
            try:
                data = self.s.recv(self.buf_size)
                print "Receiving from server: " + str(data);
            except socket.timeout, se:
                break
                
            if not data: break

    def read_json(self):
        total_data=[]
        while True:
            try:
                data = self.s.recv(self.buf_size)
            except socket.timeout, se:
                break
            if not data: break
            total_data.append(data)
        print "Receiving from server: " + str(total_data);
        return ''.join(total_data)

    def send_json(self, obj):
        self.s.send(json.dumps(obj)+'\n')
        print "Sending to server: " + json.dumps(obj) + '\n'



class EmergentSklearnRegressor(BaseEstimator, RegressorMixin):

    # All estimators should specify all the parameters that can be set
    # at the class level in their ``__init__`` as explicit keyword
    # arguments (no ``*args`` or ``**kwargs``).
    
    def __init__(self, transport, lrate=.1):

        self.lrate = lrate
        self.transport = transport
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
    
    def set_input_data(self, x, y):
        try:
            input_rows = []
            for row in x.tolist():
                input_rows.append([row])

            pprint(y)
                
            # output_rows = [[[0]*len(set(y))]]*len(input_rows)

            output_rows = []

            for row_i in range(len(input_rows)):
                cur_val = numpy.zeros((len(set(y)),1)).tolist()
                cur_row = [cur_val]
                cur_row[0][y[row_i]] = 1.0
                output_rows.append(cur_row)
                
                #output_rows[row_i][0][y[row_i]] = 1.0

            pprint(output_rows)
                
            json_obj = {"command": "SetData",
                        "table": "StdInputData",
                        "create": False,
                        "data":
                        {"columns":
                         [{"name":"Name",
                           "type": "String",
                           "values": ["HEllo World"]},
                          {"name": "Input",
                           "matrix": True,
                           "type": "float",
                           "values": input_rows},
                          {"name": "Output",
                           "matrix": True,
                           "type": "float",
                           "values": output_rows}]}}
            self.transport.send_json(json_obj)
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
        self.set_member(".networks.layers.Output.un_geom", "x", len(set(y)))
        self.set_member(".networks.layers.Output.un_geom", "y", 1)
        self.run_program("SklearnConfigNet")
        self.set_input_data(X, y)
        
        return self

    def predict(self, X):

        print "Predicting"
        return numpy.full((len(X[:,1]), 1), 1)


emer_sklearn = EmergentSklearnRegressor(transport=Transport())

input_data = sklearn.datasets.load_iris()['data']
output_data = sklearn.datasets.load_iris()['target']


emer_sklearn.fit(input_data, output_data)
# result = emer_sklearn.predict(X_test)
del emer_sklearn

# check_estimator(EmergentSklearnRegressor)


