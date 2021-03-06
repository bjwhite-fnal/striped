from nnet import Model
from nnet.trainers import SGD
import numpy as np

class ML_NNet_Worker:

        def __init__(self, params, bulk, xcolumn, ycolumn):
                self.Bulk = bulk
                self.Columns = params["columns"]

                model = Model.from_config(params["_model"]["config"])
                trainer = SGD(params["lr"], params.get("momentum", 0.5))
                model.compile(trainer=trainer)
                self.Model = model

                weights = [p for n, p in sorted(bulk.items()) if n.startswith("weight_")]
                self.Weights0 = weights
                
                self.Grads = map(np.zeros_like, weights)
                self.Samples = 0
                self.SumLoss = 0.0
                self.SumMetric = 0.0

        def preconvert_data(self, frame):
                x = frame.dot(self.Columns[0])
                y_ = frame.dot(self.Columns[1])
                n = len(x)
                return n, [x], [y]
            
                
        def frame(self, data):
                model = self.Model
                model.set_weights(self.Weights0)
                
                n, x, y_ = self.preconvert_data(data)


                #self.Job.message("run...")
                        
                model = self.Model

                with self.Trace["forward"]:
                        y, losses, metrics = model.forward(x, y_)
                        loss = losses[0]
                        metric = metrics[0]
                        self.SumLoss += loss*n
                        self.SumMetric += metric*n
                
                with self.Trace["backwards"]:
                        model.backward([y_])
                        
                        
                with self.Trace["deltas"]:
                        grads = model.get_grads()
                        for g, g1 in zip(self.Grads, grads):
                            g += g1*n
                self.Samples += n
                
        def end(self):
                out = {"grad_%020d" % (i,): g for i, g in enumerate(self.Grads)}
                out["samples"] = self.Samples
                out["sumloss"] = self.SumLoss
                out["summetric"] = self.SumMetric
                return out
