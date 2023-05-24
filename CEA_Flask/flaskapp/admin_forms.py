from flask_wtf import FlaskForm, file
from wtforms import StringField, SubmitField, BooleanField, RadioField, TextAreaField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class TrainNewModelForm(FlaskForm):
    # DocumentRelevanceRun parameters
    data = file.FileField(
            "Data (csv file)")#,
            #validators=[file.FileRequired(), file.FileAllowed(["csv"], "Only csv files are allowed.")]
            #)
    content_col = StringField(
            "Content column name",
            render_kw={"placeholder": "content"},
            )
    label_col = StringField(
            "Label column name",
            render_kw={"placeholder": "grade"},
            )
    model_type = SelectField(
            "Model type",
            choices=[("classifier", "Classification"), ("regressor", "Regression")])
    labels = SelectField(
            "Number of labels",
            choices=[(2, "2 ([0, 1])"), (4, "4 ([0, 1, 2, 3])")])
    inverse_labels = SelectField(
            "Inverse labels",
            choices=[(True, "[0, 1] -> [1, 0], [0, 1, 2, 3] -> [3, 2, 1, 0]"), (False, "Labels will stay in the same order.")])
    experiment_name = StringField(
            "Experiment name",
            description=f"Leave blank for default name (e.g 'classifier[2])'")
    run_name = StringField(
            "Run name",
            description="Leave blank to let mlflow build a custom name.")
    run_tags = StringField(
            "Run tags",
            description="Comma separated list of tags for this run.")
    run_description = TextAreaField("Run description")

    # DocumentRelevanceTrainer parameters
    checkpoint = StringField(
            "Checkpoint",
            render_kw={"placeholder": "distilbert-base-multilingual-cased"},
            description="HuggingFace base checkpoint identifier. See https://huggingface.co/models?language=fr,en&other=autotrain_compatible&sort=downloads")
    only_head = BooleanField(
            "Train only head",
            default=False,
            description="Only train the head of the model.")
    epochs = IntegerField("Number of epochs", default=5)
    batch_size = IntegerField("Batch size", default=8)
    train_size = StringField(
            "Train size",
            render_kw={"placeholder": "None"},
            description="If float, should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the train split. If int, represents the absolute number of train samples. If None, the value is automatically set to the complement of the test size.")
    test_size = StringField(
            "Test size",
            render_kw={"placeholder": "None"},
            description="If float, should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the test split. If int, represents the absolute number of test samples. If None, the value is set to the complement of the train size. If train_size is also None, it will be set to 0.25.")
    initial_lr = DecimalField(
            "Initial learning rate",
            default=5e-5,
            description="The learning rate will decay accross batches from initial learning rate to final learning_rate.")
    final_lr = DecimalField("Final learning rate", default=0)
    class_weight = StringField(
            "Class weight",
            render_kw={"placeholder": "None"},
            description="If ‘balanced’, class weights will be given by n_samples / (n_classes * np.bincount(y)). If a dictionary is given, keys are classes and values are corresponding class weights. If None is given, the class weights will be uniform.")
    submit = SubmitField("Train model!")
