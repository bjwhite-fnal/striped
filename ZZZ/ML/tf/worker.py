from striped.ml.keras_backend import ML_Keras_FitWorker
from striped.ml import ML_FitAccumulator
from keras.optimizers import SGD

class Worker(ML_Keras_FitWorker):

        def __init__(self, params, bulk, job_interface, db_interface):
                ML_Keras_FitWorker.__init__(self, params, bulk, "image", "labels", 
                        optimizer = SGD(lr=0.1, nesterov=False, momentum=0.5))

class Accumulator(ML_FitAccumulator):
        pass

