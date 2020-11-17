# Fall 2020
# Vinetech Bay Prediction model selection

import __init__
from internal import bay_pred
from tests.mocks import file_org as f

from sklearn import ensemble

if __name__ == "__main__":
    f_org = f.file_org("v", "b", "2020-01-01", 21, 21, 4)

    print("RandomForestClassifier")
    model, score = bay_pred.train_model(f_org, ensemble.RandomForestClassifier())
