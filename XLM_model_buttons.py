import os

from simpletransformers.classification import ClassificationModel, ClassificationArgs
import pandas as pd
import logging
import pprint

# Using simple transformers: https://github.com/ThilinaRajapakse/simpletransformers

datadir = "D:/temp/cookie-notice selector/output"

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


# Preparing train data
'''train_data = [
    ["Aragorn was the heir of Isildur", 1],
    ["Frodo was the heir of Isildur", 0],
]'''
with open('D:/temp/cookie-notice selector/buttons.csv', 'r', encoding="utf-8") as file:
    dataset = file.read().splitlines()

for index, d in enumerate(dataset):
    dataset[index] = d.split(';')

#print(dataset)

# Preparing train data
train_data = []
for d in dataset[355:]:
    train_data.append([d[3], d[4]])

train_df = pd.DataFrame(train_data)
train_df.columns = ["text", "labels"]

# Preparing eval data
eval_data = []
for d in dataset[180:355]:
    eval_data.append([d[3], d[4]])
eval_df = pd.DataFrame(eval_data)
eval_df.columns = ["text", "labels"]

# Optional model configuration
#model_args = ClassificationArgs(num_train_epochs=3)
model_args = ClassificationArgs()
model_args.labels_list = ["ACCEPT", "DECLINE", "MODIFY", "SAVE", "OTHER"]
model_args.output_dir = datadir
model_args.num_train_epochs = 20
model_args.learning_rate = 2e-05
model_args.eval_batch_size = 20
model_args.max_seq_length = 64
model_args.encoding = 'utf-8'
#model_args.process_count = 8
model_args.evaluate_during_training = True
model_args.use_multiprocessing_for_evaluation = False
#model_args.sliding_window = True
model_args.evaluate_each_epoch = True

if os.path.isdir(datadir):
    print("Model is present, testing all data")
    # Reuse model
    model = ClassificationModel()#"xlmroberta",
    #model = ClassificationModel("xlm-roberta-xl",
                                #datadir, use_cuda=False
    #)

else:
    print("No model is present, doing training")
    # Create a ClassificationModel
    model = ClassificationModel(
        "xlmroberta", "xlm-roberta-base", num_labels=5,
        #"xlmroberta", "facebook/xlm-roberta-xxl", #Download 40GB
        args=model_args, use_cuda=False
    )  # FutureWarning: This implementation of AdamW is deprecated and will be removed in a future version. Use the PyTorch implementation torch.optim.AdamW instead, or set `no_deprecation_warning=True` to disable this warning

    # Train the model
    model.train_model(train_df, eval_df=eval_df)
    print('--------------model trained--------------------')

    print('--------------Testing model--------------------')
    # Prepare predictions
    pred_data = []
    res_data = []
    for d in dataset[:180]:
        pred_data.append(d[3])
        res_data.append(d[4])

    # Make predictions with the model
    predictions, raw_outputs = model.predict(pred_data)

    results = []
    for index, pred in enumerate(predictions):
        # print(predictions[index], end=" - ")
        # print(res_data[index])
        results.append([pred, res_data[index], pred_data[index]])

    # pprint.pprint(results)
    right = 0
    wrong = 0
    for index, r in enumerate(results):
        if r[0] == r[1]:
            right += 1
        else:
            wrong += 1
            print(r[0], end=" - ")
            print(r[1], end=" - ")
            print(r[2])

    print("{} right".format(right))
    print("{} wrong".format(wrong))

    print('-------------Prediction data set made--------------------')

print('---------------Doing prediction on all data')
# Prepare predictions
pred_data = []
res_data = []
for d in dataset:
    pred_data.append(d[3])
    res_data.append(d[4])

# Make predictions with the model
predictions, raw_outputs = model.predict(pred_data)

results = []
for index, pred in enumerate(predictions):
    # print(predictions[index], end=" - ")
    # print(res_data[index])
    results.append([pred, res_data[index], pred_data[index]])

# pprint.pprint(results)
right = 0
wrong = 0
for index, r in enumerate(results):
    if r[0] == r[1]:
        right += 1
    else:
        wrong += 1
        print(r[0], end=" - ")
        print(r[1], end=" - ")
        print(r[2])

print("{} right".format(right))
print("{} wrong".format(wrong))

print('--------------Full prediction made--------------------')