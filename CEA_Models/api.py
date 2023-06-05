from typing import List, Union
from xmlrpc.server import SimpleXMLRPCServer
import subprocess

import mlflow
import numpy as np
import tensorflow as tf

from relevance import DocumentRelevanceRun, DocumentRelevanceTrainer, Dataloader
import summary


server = SimpleXMLRPCServer(('0.0.0.0', 3000), allow_none=True)


class RPCModels:

    def relevance_train(self, run_params, trainer_params={}, evaluate=True):
        """ Start a new training from scratch. """
        run = DocumentRelevanceRun(**run_params)
        trainer = DocumentRelevanceTrainer(**trainer_params)
        run.train_new_checkpoint(trainer)
        if evaluate:
            run.evaluate(only_head=run.trainer.train_only_head)
        return run.mlf_run.info.run_id

    def relevance_register(self, run_params, register_params={}, evaluate=True, only_head=False):
        """ Register an existing model into mlflow. """
        run = DocumentRelevanceRun(**run_params)
        run.log_existing_checkpoint(**register_params)
        if evaluate:
            run.evaluate(only_head=only_head)
        return run.mlf_run.info.run_id

    def relevance_predict(self, data: List[str], return_probas=True, run_id=None):
        """ Predict on the DocumentRelevance model.

        return_probas:
            Wether to return the probabilities (True) or the class prediction (False, default).
            Regression models will always return regression scores, but in different formats:
            a list of lists if return_probas is True, a simple list of results if return_probas
            is False.

        run_id:
            if specified, the prediction will be served by the corresponding
            run logged model. If not, the production model will be used.
        """
        if run_id:
            logged_model = f'runs:/{run_id}/model'
        else:
            logged_model = 'models:/relevance/Production'
        loaded_model = mlflow.pyfunc.load_model(logged_model)
        preds = loaded_model.predict(data)
        if not return_probas and len(preds[0]) > 1: # If return classes
            preds = np.argmax(preds, axis=1).tolist()
        elif not return_probas: # If regression
            preds = [score for sublist in preds for score in sublist]
        return preds

    def get_production_run_id(self):
        client = mlflow.MlflowClient()
        models = client.search_model_versions('name="relevance"')
        model = [model.run_id for model in models if model.current_stage == 'Production']
        if len(model) == 0: return Exception("You must have a model in Production in Mlflow.")
        return model[0]

    def gc(self):
        gc = subprocess.run(["mlflow", "gc", "--backend-store-uri", "sqlite:////mlflow/mlruns.db"], capture_output=True)
        return gc

    def summary_predict(self, text: Union[str, List[str]], min_length=30, max_length=300, model='t5-small'):
        summarizer = summary.build_model(model)
        preds = summary.predict(summarizer, text, min_length, max_length)
        return preds


server.register_instance(RPCModels())


if __name__ == '__main__':
    try:
        print('Serving...')
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting...')

