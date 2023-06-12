import os
import pathlib
import shutil
import contextlib
from dataclasses import dataclass, fields
from typing import Union, List, Dict, Optional
from functools import singledispatchmethod
from urllib.parse import unquote, urlparse

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight
import sklearn.metrics as skm
import tensorflow as tf
import matplotlib.pyplot as plt
from transformers import AutoConfig, AutoTokenizer, TFAutoModelForSequenceClassification, DataCollatorWithPadding
from datasets import Dataset, DatasetDict, load_dataset, ClassLabel
import mlflow
from codecarbon import EmissionsTracker


@dataclass
class DocumentRelevanceRun:

    data: Union[str, List[Dict]]
    content_col: str = 'content'
    label_col: str = 'grade'
    model_type: str = 'classifier'
    labels: int = 2
    inverse_labels: bool = True
    experiment: str = None
    name: str = None
    tags: List[str] = None
    description: str = None

    tmp_directory = '.temp'

    def __post_init__(self):
        if self.labels != 2 and self.labels != 4:
            raise ValueError('Parameter "labels" should be either 2 or 4.')
        if self.experiment == None:
            self.experiment = f'Relevance-{self.model_type}[{self.labels}]'

        # Load data
        self.dataloader = Dataloader()
        self.dataset = self.dataloader.load(self.data)

        # Preprocess data
        self.preprocessor = DataPreprocessor()
        self.dataset = self.preprocessor.process_columns(self.dataset, self.content_col, self.label_col)
        self.dataset = self.preprocessor.process_rows(self.dataset)

        self.logger = Logger(self.tmp_directory)

    def train_new_checkpoint(self, trainer=None):
        mlflow.set_experiment(self.experiment)

        # Prepare temp directory for artifacts
        try:
            shutil.rmtree(self.tmp_directory)
        except FileNotFoundError:
            pass
        os.makedirs(self.tmp_directory)

        self.trainer = trainer or DocumentRelevanceTrainer()
        self.tokenizer = Tokenizer(self.trainer.checkpoint)

        # Split before changing labels so that stratify applies on unmodified labels
        self.dataset = self.trainer.train_test_split(self.dataset)
        self.dataset = self.preprocessor.reduce_labels(self.dataset, self.labels)
        if self.inverse_labels:
            self.dataset = self.preprocessor.inverse_labels(self.dataset, self.labels)

        self.dataset = self.tokenizer.tokenize(self.dataset)
        self.hf_tokenizer = self.tokenizer.hf_tokenizer
        model_tmp_path = os.path.join(self.tmp_directory, 'model')
        self.hf_tokenizer.save_pretrained(model_tmp_path)

        self.train_dataset = self.preprocessor.build_tf_dataset(self.dataset['train'], self.hf_tokenizer, self.trainer.batch_size)
        self.test_dataset = self.preprocessor.build_tf_dataset(self.dataset['test'], self.hf_tokenizer, self.trainer.batch_size, shuffle=False)

        # Compute class weights
        if type(self.trainer.class_weight) == dict:
            self.trainer.class_weight = {int(k): v for k, v in self.trainer.class_weight.items()}
        class_wts = compute_class_weight(self.trainer.class_weight, classes=np.unique(self.dataset["train"]["grade"]), y=self.dataset["train"]["grade"])
        weights = {class_id: nb for class_id, nb in zip(list(np.unique(self.dataset["train"]["grade"])), list(class_wts))}

        # Build parameters dictionnary
        params = {'inverse_labels': self.inverse_labels}
        for field in fields(self.trainer):
            params[field.name] = getattr(self.trainer, field.name)

        # Fit and log model
        artifacts_path = os.path.join(self.tmp_directory, 'artifacts')
        os.makedirs(artifacts_path, exist_ok=True)
        tracker = EmissionsTracker(log_level='warning', save_to_file=True, output_dir=artifacts_path, on_csv_write='update')
        with mlflow.start_run(run_name=self.name, tags=self.tags, description=self.description) as mlf_run:
            tracker.start()
            self.trainer.fit(self.train_dataset, self.test_dataset, self.model_type, self.labels, weights, self.name, self.tags, self.description, model_tmp_path)
            tracker.stop()
            self.logger.log_model('model')
            self.logger.log_all_artifacts(artifacts_path)
            self.logger.log_params(params)
        self.mlf_run = mlf_run

    def log_existing_checkpoint(self, directory: str, base_ckpt: str = 'distilbert-base-multilingual-cased', test_size=None, batch_size=8, parameters={}):
        """ Log an already trained checkpoint to mlflow.

        directory: The folder containing the files to be logged in. It must have the
            following structure:
            - directory
            -- model
            --- tf_model.h5
            --- config.json
            -- artifacts
            --- all files in this subfolder will be logged as mlflow artifacts.

        base_ckpt: Used to build the tokenizer. Can be a checkpoint identifier on HuggingFace or a directory
            containing the custom tokenizer files.

        test_size: Number of documents to evaluate the model on.

        batch_size: Applied to test dataset.

        parameters: To be logged as mlflow parameters.
        """
        mlflow.set_experiment(self.experiment)

        # Prepare temp directory for artifacts
        try:
            shutil.rmtree(self.tmp_directory)
        except FileNotFoundError:
            pass
        shutil.copytree(directory, self.tmp_directory)

        self.tokenizer = Tokenizer(base_ckpt)
        self.hf_tokenizer = self.tokenizer.hf_tokenizer
        model_tmp_path = os.path.join(self.tmp_directory, 'model')
        self.hf_tokenizer.save_pretrained(model_tmp_path)

        if not test_size:
            test_size = self.dataset.shape[0]
        if test_size < 1:
            test_size = int(self.dataset.shape[0] * test_size)
        self.dataset = DatasetDict({'test': self.dataset.select(range(test_size))})
        self.dataset = self.preprocessor.reduce_labels(self.dataset, self.labels)
        if self.inverse_labels:
            self.dataset = self.preprocessor.inverse_labels(self.dataset, self.labels)
        self.dataset = self.tokenizer.tokenize(self.dataset)
        self.test_dataset = self.preprocessor.build_tf_dataset(self.dataset['test'], self.hf_tokenizer, batch_size, shuffle=False)

        # Build parameters dictionnary
        parameters.update({
                        'inverse_labels': self.inverse_labels,
            'checkpoint': base_ckpt,
            'test_size': test_size,
            'batch_size': batch_size})

        with mlflow.start_run(run_name=self.name, tags=self.tags, description=self.description) as mlf_run:
            self.logger.log_model('model')
            self.logger.log_params(parameters)
            self.logger.log_all_artifacts(os.path.join(self.tmp_directory, 'artifacts'))
        self.mlf_run = mlf_run

    def evaluate(self, parameters: Dict = {}, only_head=False):
        # Load model
        model_path = os.path.join(self.mlf_run.info.artifact_uri, 'model/artifacts/')
        model_path = unquote(urlparse(model_path).path)
        self.model = TFAutoModelForSequenceClassification.from_pretrained(model_path)

        # Compute evaluation predictions
        preds = self.model.predict(self.test_dataset)['logits']
        if self.model_type == 'classifier':
            predictions = preds.argmax(axis=1)
            rounded_predictions = predictions
        else:
            predictions = preds.flatten()
            rounded_predictions = np.round(predictions)

        true_values = np.array([v.numpy() for v in list(self.test_dataset.unbatch().map(lambda x, y : y))])

        # Each metric to be calculated represented as a tuple (sklearn function name, kwargs, string name to be logged)
        # see https://scikit-learn.org/stable/modules/model_evaluation.html
        metric_dict = {
                # for all classifiers
                'classifier': [('accuracy_score', {}, 'accuracy'),
                              ],
                # for binary classifiers only
                'classifier2': [('f1_score', {}, 'f1'),
                                ('precision_score', {}, 'precison'),
                                ('recall_score', {}, 'recall'),
                                ('roc_auc_score', {}, 'roc_auc'),
                               ],
                # for multiclass classifiers
                'classifier4': [#('roc_auc_score', {'multi_class': 'ovo', 'average': 'macro'}, 'roc_auc_ovo'),
                               ],
                # for regressors
                'regressor': [('mean_absolute_error', {}, 'mae'),
                              ('mean_squared_error', {}, 'mse'),
                              ('mean_squared_error', {'squared': False}, 'rmse'),
                              ('r2_score', {}, 'r2'),
                             ],
                }
        metric_prefix = 'eval_'
        # Compute metrics
        metric_list = metric_dict[self.model_type]
        metric_list.extend(metric_dict.get(f'{self.model_type}{self.labels}', []))
        metrics = {f'{metric_prefix}{metric[2]}': getattr(skm, metric[0])(true_values, predictions, **metric[1])
                   for metric in metric_list}

        # Empty temp directory
        try:
            shutil.rmtree(self.tmp_directory)
        except FileNotFoundError:
            pass
        os.makedirs(self.tmp_directory)

        # Model summary
        if only_head:
            for layer in self.model.layers:
                if not 'classifier' in layer.name: layer.trainable = False
        with open(os.path.join(self.tmp_directory, 'summary.txt'), 'w') as f:
            with contextlib.redirect_stdout(f):
                self.model.summary()
        # Datasets
        for split, dataset in self.dataset.remove_columns(['input_ids', 'attention_mask']).items():
            dataset.to_csv(os.path.join(self.tmp_directory, f'{split}_dataset.csv'))
        # Confusion matrix
        conf_matrix = skm.confusion_matrix(true_values, rounded_predictions)
        disp = skm.ConfusionMatrixDisplay(confusion_matrix=conf_matrix)
        disp.plot(cmap=plt.cm.Blues)
        confpath = os.path.join(self.tmp_directory, 'confusion_matrix.png')
        plt.savefig(confpath)
        # Errors
        dataset = self.dataset['test']
        cols_to_keep = ['author', 'content', 'grade', 'input_ids']
        dataset = dataset.remove_columns(set(dataset.column_names) - set(cols_to_keep))
        def compute_len(doc):
            return {'document length (tokens)': len(doc['input_ids'])-self.hf_tokenizer.num_special_tokens_to_add()}
        dataset = dataset.map(compute_len)
        dataset = dataset.remove_columns(['input_ids'])
        dataset = dataset.rename_column('grade', 'true_value')
        dataset = dataset.add_column(name='prediction', column=predictions)
        errors = abs(true_values-predictions)
        dataset = dataset.add_column(name='error', column=errors)
        dataset.to_csv(os.path.join(self.tmp_directory, 'errors.csv'))

        with mlflow.start_run(self.mlf_run.info.run_id) as mlf_run:
            self.logger.log_metrics(metrics)
            self.logger.log_all_artifacts(self.tmp_directory)


@dataclass
class DocumentRelevanceTrainer:
    """ Start a new training run for this model. """

    checkpoint: str = 'distilbert-base-multilingual-cased'
    train_only_head: bool = False
    epochs: int = 5
    batch_size: int = 8
    train_size: Union[float, int] = None
    test_size: Union[float, int] = None
    initial_lr: float = 5e-5
    final_lr: float = 0
    class_weight: Union[str, Dict] = None # "balanced"/None or {0:w1, 1:w2, ...}

    def train_test_split(self, dataset):
        dataset = dataset.train_test_split(train_size=self.train_size, test_size=self.test_size, stratify_by_column='grade', seed=12345)
        return dataset

    def fit(self, train_dataset, test_dataset, model_type, labels, weights, name, tags, description, tmp_model):
        if model_type == 'classifier':
            _labels = labels
            self.metrics = ['accuracy']
            self.loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        elif model_type ==  'regressor':
            _labels = 1
            self.metrics = ['mse']
            self.loss = tf.keras.losses.MeanAbsoluteError()
        else:
            raise ValueError('Argument model_type should be one of "classifier" or "regressor"')

        model = TFAutoModelForSequenceClassification.from_pretrained(self.checkpoint, num_labels=_labels)
        num_train_steps = len(train_dataset) * self.epochs
        lr_scheduler = tf.keras.optimizers.schedules.PolynomialDecay(
                initial_learning_rate=self.initial_lr,
                end_learning_rate=self.final_lr,
                decay_steps=num_train_steps)
        optimizer = tf.keras.optimizers.Adam(learning_rate=lr_scheduler)

        class SaveBestModelCallback(tf.keras.callbacks.Callback):
            history = []
            def on_epoch_end(self2, epoch, logs={}):
                self2.history.append(logs['val_loss'])
                if logs['val_loss'] == min(self2.history):
                    self2.model.save_pretrained(tmp_model)

        class LogEpochMetrics(tf.keras.callbacks.Callback):
            def on_epoch_end(self2, epoch, logs={}):
                mlflow.log_metrics(logs, epoch)

        if self.train_only_head:
            for layer in model.layers:
                if not 'classifier' in layer.name: layer.trainable = False

        model.compile(
                optimizer=optimizer,
                loss=self.loss,
                metrics=self.metrics)

        self.history = model.fit(
                train_dataset,
                validation_data=test_dataset,
                epochs=self.epochs,
                class_weight=weights,
                callbacks=[SaveBestModelCallback(), LogEpochMetrics()])


class DocumentRelevancePredicter(mlflow.pyfunc.PythonModel):

    def load_context(self, context: mlflow.pyfunc.PythonModelContext):
        config_file = os.path.dirname(context.artifacts['config'])
        self.config = AutoConfig.from_pretrained(config_file)
        self.hf_tokenizer = AutoTokenizer.from_pretrained(config_file)
        self.model = TFAutoModelForSequenceClassification.from_pretrained(config_file, config=self.config)

    def predict(self, context: mlflow.pyfunc.PythonModelContext, data):
        """
        data:
            ['First document content', 'Second document content']

        returns:
            regression: a list of lists containing float regression scores.
            classification: a list of lists containing probabilities (softmax output)
        """
        data = self.hf_tokenizer(data, padding=True, return_tensors='tf', truncation=True)
        results = self.model(data)['logits']
        if results.shape[1] > 1: # If classification
            results = tf.math.softmax(results)
        results = results.numpy().tolist()
        return results


class Dataloader:
    """ Load data from various formats, return a dataset object. """

    @singledispatchmethod
    def load(self, data):
        """ Default implementation. """
        raise NotImplementedError(f'This data format ({type(data)}) cannot be loaded.')

    @load.register(list)
    def _(self, data):
        """ Load data from a list of dictionnaries. """
        return Dataset.from_list(data)

    @load.register(str)
    def _(self, data):
        """ Load data from a csv file. """
        return load_dataset('csv', data_files=data, split='train')


class DataPreprocessor:
    """ Preprocess a dataset into the right format. """

    def process_columns(self, dataset, content_col, label_col):
        if 'content' not in dataset.column_names:
            dataset = dataset.rename_column(content_col, 'content')
        if 'grade' not in dataset.column_names:
            dataset = dataset.rename_column(label_col, 'grade')
        dataset = dataset.cast_column("grade", ClassLabel(num_classes=4))
        return dataset

    def process_rows(self, dataset):
        dataset = dataset.filter(
                lambda doc : doc['content'] is not None
                and doc['grade'] is not None
                and doc['grade'] != 0)
        return dataset

    def reduce_labels(self, dataset, labels):
        def change_labels(doc):
            if labels == 2:
                if doc['grade'] == 2: doc['grade'] = 1
                elif doc['grade'] == 3 or doc['grade'] == 4: doc['grade'] = 2
            return {'grade': doc['grade']-1}
        dataset = dataset.map(change_labels)
        return dataset

    def inverse_labels(self, dataset, labels):
        def inverse(doc):
            return {'grade': labels-doc['grade']-1}
        dataset = dataset.map(inverse)
        return dataset

    def build_tf_dataset(self, split, hf_tokenizer, batch_size=8, shuffle=True):
        data_collator = DataCollatorWithPadding(tokenizer=hf_tokenizer, return_tensors='tf')
        split_dataset = split.to_tf_dataset(
                columns=['attention_mask', 'input_ids'],
                label_cols=['grade'],
                shuffle=shuffle,
                collate_fn=data_collator,
                batch_size=batch_size)
        return split_dataset


class Tokenizer:

    def __init__(self, checkpoint):
        self._hf_tokenizer = AutoTokenizer.from_pretrained(checkpoint)

    @property
    def hf_tokenizer(self):
        return self._hf_tokenizer

    def tokenize(self, dataset):
        def tokenize_content(doc):
            return self._hf_tokenizer(doc['content'], truncation=True)
        dataset = dataset.map(tokenize_content, batched=True)
        return dataset


class Logger:

    def __init__(self, tmp_directory):
        self.tmp_directory = tmp_directory

    def log_model(self, dest_path):
        """ Log the model and all other files in tmp_directory/model. """
        src_path = os.path.join(self.tmp_directory, 'model')
        artifacts = {
                pathlib.Path(file).stem: os.path.join(src_path, file)
                for file in os.listdir(src_path)
                if not os.path.basename(file).startswith('.')}

        mlflow.pyfunc.log_model(
                dest_path,
                python_model=DocumentRelevancePredicter(),
                artifacts=artifacts)

    def log_params(self, params: Dict):
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict):
        mlflow.log_metrics(metrics)

    def log_all_artifacts(self, path):
        mlflow.log_artifacts(path)


if __name__ == '__main__':
    run = DocumentRelevanceRun(
            model_type='classifier',
            data='CFR2122/LinkedInPosts_20220521_2.csv',
            label_col='note',
            labels=2)
    trainer = DocumentRelevanceTrainer(
            train_size=10,
            test_size=30,
            batch_size=10,
            epochs=1,
            train_only_head=False,
            class_weight=None)
    run.train_new_checkpoint(trainer)

    run = DocumentRelevanceRun(
            data='CFR2122/test_dataset.csv',
            label_col='note',
            labels=2,
            inverse_labels=True,
            name='cfr2122')

    run.train_new_checkpoint(trainer)
    # run.log_existing_checkpoint('CFR2122',
    #         parameters={'initial_lr': 'hfbfuzb'},)


    run.evaluate()


    # logged_model = f'runs:/{run.mlf_run.info.run_id}/model'
    # loaded_model = mlflow.pyfunc.load_model(logged_model)
    # preds = loaded_model.predict(['Ecologie! Eco-innovation.', 'Tartiflette et pédalo'])
    # print(preds)
