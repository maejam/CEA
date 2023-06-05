from typing import Union
from flask import flash
from flask_wtf import FlaskForm, file
from wtforms import StringField, SubmitField, BooleanField, RadioField, TextAreaField, SelectField, IntegerField, FloatField, DecimalField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange


class SettingsForm(FlaskForm):
    batch_size = IntegerField(
            "Batch size for predictions",
            validators=[Optional()],
            render_kw={"placeholder": 100},
            )
    predict_all = SubmitField(
            "Compute predictions for all documents",
            description="If you encounter a '[Errno 111] Connection refused' error, try reducing the batch size."
            )
    empty_bin = SubmitField(
            "Empty Mlflow recycle bin",
            description="When a run or experiment is deleted in mlflow, it is not deleted from the disk. Use this button to run garbage collection.",
            )


class ModelForm(FlaskForm):
    # DocumentRelevanceRun parameters
    content_col = StringField(
            "Content column name",
            render_kw={"placeholder": "content"},
            )
    label_col = StringField(
            "Label column name",
            render_kw={"placeholder": "note"},
            )
    model_type = SelectField(
            "Model type",
            choices=[("classifier", "Classification"), ("regressor", "Regression")])
    labels = SelectField(
            "Number of labels",
            choices=[2, 4],
            coerce=int,
            description="2=>[0, 1] / 4=>[0, 1, 2, 3]")
    inverse_labels = SelectField(
            "Inverse labels",
            choices=[True, False],
            coerce=bool,
            description="[0, 1]=>[1, 0] / [0, 1, 2, 3]=>[3, 2, 1, 0]")
    experiment_name = StringField(
            "Experiment name",
            description=f"Leave blank for default name (e.g. 'classifier[2])'")
    run_name = StringField(
            "Run name",
            description="Leave blank to let mlflow build a custom name.")
    run_tags = StringField(
            "Run tags",
            description="Comma separated list of key: value tags for this run (e.g. 'key1: tag1, key2: tag2').")
    run_description = TextAreaField("Run description")

    # DocumentRelevanceTrainer parameters
    only_head = BooleanField(
            "Train only head",
            default=False,
            description="Train only the head of the model.")
    batch_size = IntegerField(
            "Batch size",
            validators=[NumberRange(min=1, message="Must be positive.")],
            default=8)
    evaluate = BooleanField(
            "Evaluate model",
            default=True,
            )

    def validate_dataloader(self, dataloader):
        if self.dataloader.data == "fromcsv" and self.datafile.data == None:
            msg = "If you choose to load data from a csv file, you should provide such a file."
            raise ValidationError(msg)

    def validate_train_size(self, train_size):
        if train_size.data == None: return True
        if train_size.data >= 1 and train_size.data < 4:
            raise ValidationError("Train size should be at least 4 documents.")

    def validate_test_size(self, test_size):
        if test_size.data == None: return True
        if test_size.data >= 1 and test_size.data < 4:
            raise ValidationError("Test size should be at least 4 documents.")

    def validate_class_weight(self, class_weight):
        if "," in class_weight.data:
            weights = class_weight.data.split(",")
            try:
                weights = [float(weight) for weight in weights]
            except ValueError:
                raise ValidationError("All values should be numeric.")
            if len(weights) != self.labels.data:
                raise ValidationError(f"You should provide as many weight values as labels ({self.labels.data})")

    def validate_run_tags(self, run_tags):
        if run_tags.data == "": return True
        tags = run_tags.data.split(",")
        for idx, tag in enumerate(tags):
            if ":" not in tag: raise ValidationError(f"Tag #{idx+1} is not a key: value pair.")


class TrainNewModelForm(ModelForm):
    datafile = file.FileField(
            "Data (csv file)",
            validators=[Optional(), file.FileAllowed(["csv"], "Only csv files are allowed")],
            default=None
            )
    dataloader = RadioField(
            choices=[("fromdb", "Load documents from database"),
                     ("fromcsv", "Load documents from csv file")],
            default="fromdb"
            )
    train_size = FloatField(
            "Train size",
            validators=[Optional()],
            render_kw={"placeholder": None},
            description="If float, should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the train split. If int, represents the absolute number of train samples. If None, the value is automatically set to the complement of the test size.")
    test_size = FloatField(
            "Test size",
            validators=[Optional()],
            render_kw={"placeholder": None},
            description="If float, should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the test split. If int, represents the absolute number of test samples. If None, the value is set to the complement of the train size. If train_size is also None, it will be set to 0.25.")
    epochs = IntegerField(
            "Number of epochs",
            validators=[NumberRange(min=1, message="Must be positive.")],
            default=5)
    checkpoint = StringField(
            "Checkpoint",
            render_kw={"placeholder": "distilbert-base-multilingual-cased"},
            )
    class_weight = StringField(
            "Class weight",
            render_kw={"placeholder": None},
            description="If ‘balanced’, class weights will be given by n_samples / (n_classes * np.bincount(y)). Enter comma-separated numbers to specify custom weights for each class (after inversion if True) from 0 to #labels. If None is given, the class weights will be uniform.")
    initial_lr = FloatField(
            "Initial learning rate",
            default=5e-5,
            description="The learning rate will decay accross batches from initial learning rate to final learning_rate.")
    final_lr = FloatField("Final learning rate", default=0)
    train = SubmitField("Train model")


class RegisterModelForm(ModelForm):
    modelfile = file.FileField(
            "Model (h5 file)",
            validators=[DataRequired(), file.FileAllowed(["h5"], "Only h5 files are allowed")],
            )
    configfile = file.FileField(
            "Config file (config.json file)",
            validators=[DataRequired(), file.FileAllowed(["json"], "Only json files are allowed")],
            )
    dataloader = RadioField(
            choices=[("fromdb", "Load documents from database"),
                     ("fromcsv", "Load documents from csv file")],
            default="fromcsv"
            )
    datafile = file.FileField(
            "Evaluation data (csv file)",
            validators=[Optional(), file.FileAllowed(["csv"], "Only csv files are allowed")],
            default=None
            )
    train_size = FloatField(
            "Train size",
            validators=[Optional()],
            render_kw={"placeholder": None},
            description="This parameter has no impact. Included only for registration purposes.")
    test_size = FloatField(
           "Test size",
            validators=[Optional()],
            render_kw={"placeholder": None},
            description="If float, should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the test split. If int, represents the absolute number of test samples. If None, the whole dataset will be used for evaluation.")
    epochs = IntegerField(
            "Number of epochs",
            validators=[NumberRange(min=1, message="Must be positive.")],
            description="This parameter has no impact. Included only for registration purposes.",
            default=5)
    checkpoint = StringField(
            "Checkpoint",
            render_kw={"placeholder": "distilbert-base-multilingual-cased"},
            description="Used to instantiate the corresponding tokenizer."
            )
    class_weight = StringField(
            "Class weight",
            render_kw={"placeholder": None},
            description="This parameter has no impact. Included only for registration purposes."
            )
    initial_lr = FloatField(
            "Initial learning rate",
            default=5e-5,
            description="This parameter has no impact. Included only for registration purposes.")
    final_lr = FloatField(
            "Final learning rate",
            default=0,
            description="This parameter has no impact. Included only for registration purposes.")
    artifacts = MultipleFileField(
            "Additional artifacts",
            description="Register additional artifacts along with your model. You can include multiple files."
            )
    register = SubmitField("Register model")
