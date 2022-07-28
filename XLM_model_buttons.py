import os
import random

from simpletransformers.classification import ClassificationModel, ClassificationArgs
import pandas as pd
import logging

# Using simple transformers: https://github.com/ThilinaRajapakse/simpletransformers

#datadir = "D:/temp/cookie-notice selector/output"

# Voorbereiding voor machine learning models, anders toont het te veel data in console
logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

# Variabelen voorbereiden
NUMBER_OF_RUNS = 1

# Preparing dataset
with open('D:/Documenten/Maarten/Open universiteit/VAF/DATA/Classification file for buttons.csv', 'r', encoding="utf-8") as file:
    dataset = file.read().splitlines()
for index, d in enumerate(dataset):
    dataset[index] = d.split(';')
    dataset[index][3] = dataset[index][3].lower()

# Start de training sessie(s)
for i in range(NUMBER_OF_RUNS):
    datadir = "D:/temp/training model buttons/" + str(i) + "/"
    if not os.path.isdir(datadir):
        dataset_shuffle = random.sample(dataset, len(dataset))
        print(f'Start training {i}')

        training_group = int(len(dataset_shuffle) * 0.7)
        eval_group = int((len(dataset_shuffle) - training_group) / 2)
        prediction_group = len(dataset_shuffle) - training_group - eval_group

        print(f"Total length of dataset: {len(dataset_shuffle)}")
        print(f"Length of training_group: {training_group}")
        print(f"Length of eval group: {eval_group}")
        print(f"Length of prediction group: {prediction_group}")

        # Preparing train data
        train_data = []
        for d in dataset_shuffle[:training_group]:
            train_data.append([d[3].lower(), d[4]])

        train_df = pd.DataFrame(train_data)
        train_df.columns = ["text", "labels"]

        # Preparing eval data
        eval_data = []
        for d in dataset_shuffle[training_group:training_group + eval_group]:
            eval_data.append([d[3].lower(), d[4]])
        eval_df = pd.DataFrame(eval_data)
        eval_df.columns = ["text", "labels"]

        # Optional model configuration
        model_args = ClassificationArgs()
        model_args.num_train_epochs = 20
        model_args.labels_list = ["ACCEPT", "DECLINE", "MODIFY", "SAVE", "OTHER"]
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

        #Early stopping metric
        model_args.use_early_stopping = True
        model_args.early_stopping_delta = 0.001
        model_args.early_stopping_metric = "mcc"
        model_args.early_stopping_metric_minimize = False
        model_args.early_stopping_patience = 5
        model_args.evaluate_during_training_steps = int(training_group/model_args.train_batch_size/3*4)

        print(f'No model preset, doing training {i}')

        # Create a ClassificationModel
        model = ClassificationModel(
            "xlmroberta", "xlm-roberta-base", num_labels=5,
            args=model_args, use_cuda=False
        )  # FutureWarning: This implementation of AdamW is deprecated and will be removed in a future version. Use the PyTorch implementation torch.optim.AdamW instead, or set `no_deprecation_warning=True` to disable this warning

        # Train the model
        model.train_model(train_df, eval_df=eval_df)
        print('--------------model trained--------------------')

        # Prepare predictions for the dataset
        pred_data = []
        res_data = []
        for d in dataset_shuffle[training_group + eval_group:training_group + eval_group + prediction_group]:
            pred_data.append(d[3].lower())
            res_data.append(d[4])

        print('--------------Doing predictions on small dataset--------------------')

        # Make predictions with the model
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

        print('--------------prediction made on small dataset--------------------')


    print('--------------Doing predictions on full dataset--------------------')

    # Reuse model
    model = ClassificationModel("xlmroberta", datadir, use_cuda=False)

    # Prepare predictions for the whole dataset
    pred_data = []
    res_data = []
    for d in dataset:
        pred_data.append(d[3].lower())
        res_data.append(d[4])

    # Make predictions with the model
    predictions, raw_outputs = model.predict(pred_data)

    #results = []
    right = 0
    wrong = 0
    for index in range(len(pred_data)):
        if res_data[index] == predictions[index]:
            right += 1
        else:
            wrong += 1
            print(index, end=" - ")
            print(pred_data[index], end=" - ")
            print(res_data[index], end=" - ")
            print(predictions[index])

    print("{} right".format(right))
    print("{} wrong".format(wrong))

    print('--------------prediction made on full dataset--------------------')