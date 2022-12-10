import random
import numpy as np
import matplotlib.pyplot as plt


class DistributedLinearRegression():

    def __init__(self):
        self.theta = None
        self.cost_list = []


    def initialize(self, dim):
        # +1 for bias term
        self.theta = np.random.rand(dim+1)
    
    
    def gradient_descent(self, x, y, lr, num_epochs):
        x = np.c_[np.ones(x.shape[0]), x]
        m = len(y)
        for i in range(num_epochs):
            prediction = np.dot(x, self.theta)
            error = prediction - y
            cost = 1/(2*m) * np.dot(error.T, error)
            self.cost_list.append(cost)
            self.theta = self.theta - (lr * (1/m) * np.dot(x.T, error))


    def fit(self, x, y, lr = 0.05, num_epochs = 10):
        self.initialize(x.shape[1])
        self.gradient_descent(x, y, lr, num_epochs)
    
 
    def predict(self, x):
        # Batch inputs only
        x = np.c_[np.ones(x.shape[0]), x]
        return np.dot(x, self.theta)

    
    def get_weights(self):
        return self.theta

 
    def from_weights(self, thetas):
        self.theta = thetas.mean(axis = 0)
