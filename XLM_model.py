import os

from simpletransformers.classification import ClassificationModel, ClassificationArgs
import pandas as pd
import logging
import pprint

# Using simple transformers: https://github.com/ThilinaRajapakse/simpletransformers

datadir = "D:/temp/cookie-notice selector backup/output"

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


# Preparing train data
'''train_data = [
    ["Aragorn was the heir of Isildur", 1],
    ["Frodo was the heir of Isildur", 0],
]'''
with open('D:/temp/cookie-notice selector backup/classification3.csv', 'r', encoding="utf-8") as file:
    dataset = file.read().splitlines()

for index, d in enumerate(dataset):
    dataset[index] = d.split(';')

#print(dataset)

# Preparing train data
train_data = []
#for d in dataset[:450]:
for d in dataset[200:]:
    train_data.append([d[3], d[4]])

train_df = pd.DataFrame(train_data)
train_df.columns = ["text", "labels"]

# Preparing eval data
eval_data = []
#for d in dataset[450:550]:
for d in dataset[100:200]:
    eval_data.append([d[3], d[4]])
eval_df = pd.DataFrame(eval_data)
eval_df.columns = ["text", "labels"]

# Optional model configuration
model_args = ClassificationArgs(num_train_epochs=1)
model_args.labels_list = ["True", "False"]
model_args.output_dir = datadir
model_args.num_train_epochs = 2
model_args.learning_rate = 2e-05
model_args.eval_batch_size = 1
model_args.max_seq_length = 512
model_args.encoding = 'utf-8'
#model_args.process_count = 8
model_args.evaluate_during_training = True
model_args.use_multiprocessing_for_evaluation = False
#model_args.sliding_window = True

if os.path.isdir(datadir):
    # Reuse model
    model = ClassificationModel("xlmroberta",
    #model = ClassificationModel("xlm-roberta-xl",
                                datadir, use_cuda=False
    )

    # Prepare predictions
    pred_data = []
    res_data = []
    # for d in dataset[550:650]:
    for d in dataset:
        pred_data.append(d[3])
        res_data.append(d[4])

else:
    # Create a ClassificationModel
    model = ClassificationModel(
        "xlmroberta", "xlm-roberta-base",
        #"xlmroberta", "facebook/xlm-roberta-xxl", #Download 40GB
        args=model_args, use_cuda=False
    )  # FutureWarning: This implementation of AdamW is deprecated and will be removed in a future version. Use the PyTorch implementation torch.optim.AdamW instead, or set `no_deprecation_warning=True` to disable this warning

    # Train the model
    model.train_model(train_df, eval_df=eval_df)
    print('--------------model trained--------------------')

    # Prepare predictions
    pred_data = []
    res_data = []
    # for d in dataset[550:650]:
    for d in dataset[:100]:
        pred_data.append(d[3])
        res_data.append(d[4])

# Evaluate the model
'''model_args.use_multiprocessing = False
model_args.use_multiprocessing_for_evaluation = False
result, model_outputs, wrong_predictions = model.eval_model(eval_df)
#print(result)
#print('-------------------------------------------------')
#print(model_outputs)
#print('-------------------------------------------------')
#pprint.pprint(wrong_predictions)
print('--------------model evaluated--------------------')'''



'''eval_df = pd.DataFrame(eval_data)
eval_df.columns = ["text", "labels"]'''

# Make predictions with the model
predictions, raw_outputs = model.predict(pred_data)

results = []
for index, pred in enumerate(pred_data):
    print(predictions[index], end=" - ")
    print(res_data[index])
    results.append([predictions[index], res_data[index]])

print("--------------------------------------------------")

#pprint.pprint(results)
right = 0
wrong = 0
for index, r in enumerate(results):
    if r[0] == r[1]:
        right += 1
    else:
        wrong += 1
        print(dataset[index])


print("{} right".format(right))
print("{} wrong".format(wrong))

print('--------------prediction made--------------------')