import os
import random

from simpletransformers.classification import ClassificationModel, ClassificationArgs # https://github.com/ThilinaRajapakse/simpletransformers
import pandas as pd
import logging

def main(number_of_runs, classification_filename, model_savedir, model_type):
    # Voorbereiding voor machine learning models, anders toont het te veel data in console
    logging.basicConfig(level=logging.INFO)
    transformers_logger = logging.getLogger("transformers")
    transformers_logger.setLevel(logging.WARNING)

    # Preparing dataset
    with open(classification_filename, 'r', encoding="utf-8") as file:
        dataset = file.read().splitlines()
    for index, d in enumerate(dataset):
        dataset[index] = d.split(';')
        dataset[index][3] = dataset[index][3].lower()

    training_group_size = int(len(dataset) * 0.7)
    eval_group_size = int((len(dataset) - training_group_size) / 2)
    prediction_group_size = len(dataset) - training_group_size - eval_group_size

    print(f"Total length of dataset: {len(dataset)}")
    print(f"Length of training group: {training_group_size}")
    print(f"Length of eval group: {eval_group_size}")
    print(f"Length of prediction group: {prediction_group_size}")
    print('')

    # Start de training sessie(s)
    for i in range(number_of_runs):
        datadir = model_savedir + str(i) + "/"

        # Optional model configuration
        model_args = prepare_options(datadir, training_group_size, model_type)

        # Training session if no model is present in this dir
        if not os.path.isdir(datadir):
            print(f'Doing new prediction in {datadir}')
            training_session(i, dataset, datadir, model_args, training_group_size, eval_group_size, prediction_group_size)

        # Full prediction afterwards or if model is already present
        full_predictions(dataset, datadir, training_group_size, eval_group_size, prediction_group_size)


def prepare_options(datadir, training_group, model_type):
    model_args = ClassificationArgs()
    if model_type == "cookie dialog":
        model_args.num_train_epochs = 5
        model_args.labels_list = ["True", "False"]
        model_args.max_seq_length = 512
    elif model_type == "buttons":
        model_args.num_train_epochs = 20
        model_args.labels_list = ["ACCEPT", "DECLINE", "MODIFY", "SAVE", "OTHER"]
        model_args.max_seq_length = 64

    model_args.output_dir = datadir
    model_args.cache_dir = datadir + "cache/"

    model_args.learning_rate = 2e-05
    model_args.train_batch_size = 32
    model_args.eval_batch_size = 32
    model_args.max_seq_length = 64
    model_args.encoding = 'utf-8'
    model_args.evaluate_during_training = True
    model_args.evaluate_during_training_verbose = True
    model_args.use_multiprocessing_for_evaluation = False
    model_args.evaluate_each_epoch = True
    model_args.do_lower_case = True
    model_args.save_model_every_epoch = False
    model_args.save_steps = -1
    model_args.save_eval_checkpoints = False
    model_args.best_model_dir = datadir + "best_model/"
    model_args.save_best_model = True

    # Early stopping metric
    model_args.use_early_stopping = True
    model_args.early_stopping_delta = 0.001
    model_args.early_stopping_metric = "mcc"
    model_args.early_stopping_metric_minimize = False
    model_args.early_stopping_patience = 5
    model_args.evaluate_during_training_steps = int(training_group / model_args.train_batch_size / 3 * 4)

    return model_args

def training_session(i, dataset, datadir, model_args, training_group_size, eval_group_size, prediction_group_size):
    dataset_shuffle = random.sample(dataset, len(dataset))
    print(f'Start training {i}')

    # Preparing train data
    train_data = []
    for d in dataset_shuffle[:training_group_size]:
        train_data.append([d[3].lower(), d[4]])

    train_df = pd.DataFrame(train_data)
    train_df.columns = ["text", "labels"]

    # Preparing eval data
    eval_data = []
    for d in dataset_shuffle[training_group_size:training_group_size + eval_group_size]:
        eval_data.append([d[3].lower(), d[4]])
    eval_df = pd.DataFrame(eval_data)
    eval_df.columns = ["text", "labels"]

    print(f'No model preset, doing training {i}')

    # Create a ClassificationModel
    model = ClassificationModel(
        "xlmroberta", "xlm-roberta-base", num_labels=len(model_args.labels_list),
        args=model_args, use_cuda=False
    )  # FutureWarning: This implementation of AdamW is deprecated and will be removed in a future version. Use the PyTorch implementation torch.optim.AdamW instead, or set `no_deprecation_warning=True` to disable this warning

    # Train the model
    model.train_model(train_df, eval_df=eval_df)
    print('--------------model trained--------------------')


    print('--------------Doing predictions on small dataset--------------------')

    # Make predictions with the model
    make_prediction(dataset_shuffle, model, training_group_size, eval_group_size, prediction_group_size)

    print('--------------prediction made on small dataset--------------------')

def make_prediction(dataset, model, training_group_size, eval_group_size, prediction_group_size):
    # Prepare predictions for the dataset
    pred_data = []
    res_data = []
    for d in dataset[training_group_size + eval_group_size:training_group_size + eval_group_size + prediction_group_size]:
        pred_data.append(d[3].lower())
        res_data.append(d[4])

    # Do predictions
    predictions, raw_outputs = model.predict(pred_data)

    # Analyse results
    right = 0
    wrong = 0
    for index in range(len(pred_data)):
        # print(predictions[index], end=" - ")
        # print(res_data[index])
        # results.append([predictions[index], res_data[index]])
        if res_data[index] == predictions[index]:
            right += 1
        else:
            wrong += 1
            print(index, end=" - ")
            print(pred_data[index], end=" - ")
            print(res_data[index], end=" - ")
            print(predictions[index])


def full_predictions(dataset, datadir, training_group_size, eval_group_size, prediction_group_size):
    print('--------------Doing predictions on full dataset--------------------')

    # Reuse model
    model = ClassificationModel("xlmroberta", datadir, use_cuda=False)

    # Prepare predictions for the whole dataset
    make_prediction(dataset, model, training_group_size, eval_group_size, prediction_group_size)

    print('--------------prediction made on full dataset--------------------')


if __name__ == '__main__':
    main()
