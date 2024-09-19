#!/usr/bin/env python3

import pandas as pd
from wnaffect import WNAffect # 3rd party open source module that mapped WNAffect from WN
import sqlite3
from textblob import TextBlob # type: ignore
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments # type: ignore
from datasets import load_dataset, load_metric # type: ignore
from sklearn.model_selection import train_test_split

month = input("Which month's sentiment analysis do you want to do?(yyyy-mm format e.g.2016-06)\n>")

cnx = sqlite3.connect("%s_stories.db" %(month))
df = pd.read_sql("SELECT * FROM [%s_stories]" %(month), cnx)


stories_df = df[df["lemmas"].apply(lambda x: len(eval(x))>=50)] # Getting rid of stories with less than 50 lemmas
new_stories_df = stories_df.reset_index(drop=True) # resetting index and starting from 0 again

# new_stories_df['date'] = pd.to_datetime(new_stories_df['date'])

# Textblob Polarity Analysis
stories_lst = new_stories_df["story_itself"].tolist()
pos_tag_lst = new_stories_df['pos_tags'].tolist()


def sentimentAnalysis(story):
    # This function takes the words of a story as input and gives a polarity and a subjectivity score as output
    blob = TextBlob(story)
    for sentence in blob.sentences:
        return sentence.sentiment

story_sentiments = [sentimentAnalysis(story) for story in stories_lst]

if len(story_sentiments) == len(new_stories_df):
    stories_emotion_df = new_stories_df

stories_emotion_df["polarity_sentiments(polarity, subjectivity)"] = story_sentiments


# WN-Affect based sentiment analysis

wna = WNAffect('wordnet-1.6/', 'wn-domains-3.2/')

new_lista = [stories_lst[i][2:-2].split() for i in range(len(stories_lst))]
new_listb = [pos_tag_lst[i][2:-2].split("', '") for i in range(len(pos_tag_lst))]

stories_pos_tag_together_list = [list(zip(new_lista[i], new_listb[i])) for i in range(len(stories_lst))] # Building a list of tuples(word, pos_tag)

emotion_stories = []
senti_stories = stories_pos_tag_together_list[:]

for story in senti_stories:
    emotion_story = []
    for word, pos in story:
        emo = wna.get_emotion(word, pos)
        if emo == None:
            continue
        else:
            root_emotion = ' -> '.join([emo.get_level(i).name for i in range(emo.level + 1)]) # Getting the emotion from the root level to the current level
            emotion_story.append(root_emotion)

    emotion_stories.append(emotion_story)

if len(stories_emotion_df) == len(emotion_stories):
    stories_emotion_df["wordnet_sentiments"] = emotion_stories

node_emotion_types = ['positive', 'negative', 'ambiguous', 'neutral-emotion']

subnode_emotion_types = ['gratitude', 'levity', 'fearlessness', 'positive-fear', 'positive-expectation',
                        'self-pride', 'affection', 'enthusiasm', 'positive-hope', 'calmness', 'love', 'joy',
                        'liking', 'ingratitude', 'daze', 'humility', 'compassion', 'despair', 'shame', 'anxiety',
                        'negative-fear', 'general-dislike', 'sadness', 'surprise', 'thing', 'pensiveness', 'gravity',
                        'ambiguous-fear', 'ambiguous-expectation', 'ambiguous-agitation', 'surprise', 'apathy',
                        'neutral-unconcern']

# Counting each node emotion types and building a column for each type
d = {k: stories_emotion_df.wordnet_sentiments.apply(lambda x: ' '.join(x).count(k)) for k in node_emotion_types}
wordnet_sentiment_df = stories_emotion_df.assign(**d)

temp_df = wordnet_sentiment_df
temp_df['node_emotion_vector'] = temp_df['positive'] + temp_df['negative']+ temp_df['ambiguous'] + temp_df['neutral-emotion']

# Counting each subnode emotion types and building a column for each type
e = {k: stories_emotion_df.wordnet_sentiments.apply(lambda x: ' '.join(x).count(k)) for k in subnode_emotion_types}
wordnet_sentiment_df = stories_emotion_df.assign(**e)

node_temp_df = temp_df.loc[:,'ambiguous':'node_emotion_vector']

sub_temp_df = wordnet_sentiment_df.loc[:, 'affection':'thing']
sub_cols = list(sub_temp_df.columns)
sub_temp_df['subnode_emotion_vector'] = sub_temp_df[sub_cols].sum(axis=1)

# Concatenating them to get all the nodes and subnodes counts as an individual column
sentiment_df = pd.concat([node_temp_df, sub_temp_df], axis=1)


final_sentiment_df = pd.concat([stories_emotion_df, sentiment_df], axis=1)

# Getting the probabilities of each node emotion types
final_sentiment_df['positive/node_vector'] = final_sentiment_df['positive']/final_sentiment_df['node_emotion_vector']
final_sentiment_df['negative/node_vector'] = final_sentiment_df['negative']/final_sentiment_df['node_emotion_vector']
final_sentiment_df['ambiguous/node_vector'] = final_sentiment_df['ambiguous']/final_sentiment_df['node_emotion_vector']
final_sentiment_df['neutral/node_vector'] = final_sentiment_df['neutral-emotion']/final_sentiment_df['node_emotion_vector']
final_sentiment_df['node_vector/subnode_vector'] = final_sentiment_df['node_emotion_vector']/final_sentiment_df['subnode_emotion_vector']

another_cnx = sqlite3.connect('%s_sentiments_annotated.db' %(month))
final_sentiment_df.to_csv("%s_stories_sentiment_annotated.csv" %(month))
df_sentiment = pd.read_csv('%s_stories_sentiment_annotated.csv' %(month), index_col=0 )
df_sentiment.to_sql('%s_sentiments_annotated.db' %(month), another_cnx)

# Load a pre-trained tokenizer and model
tokenizer = BertTokenizer.from_pretrained('distilbert-base-uncased')
model = BertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)
df_meta_data = pd.DataFrame(data, columns=cols) # type: ignore
# Load your custom dataset (or a placeholder dataset for this example)
# Ensure the dataset has two columns: 'text' and 'label'
dataset = load_dataset( data_files=df_meta_data )  # Example CSV file with 'text' and 'label'
dataset = dataset[train] # type: ignore
cnx = sqlite3.connect("%s_stories.db" %(month))
df = pd.read_sql("SELECT * FROM [%s_stories]" %(month), cnx)

sample_size = input("How many stories do you want as a sample?\n>")
sample_stories = df.sample(int(sample_size))

another_cnx = sqlite3.connect("%s_sample_stories.db" %(month))
sample_stories.to_sql("%s_sample_stories" %(month), another_cnx)
# Tokenize the text data
def preprocess_function(examples):
    return tokenizer(examples[df], truncation=True, padding=True, max_length=128)

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# Split the dataset into train and validation sets
train_dataset, val_dataset = train_test_split(tokenized_dataset, test_size=0.2)

# Define the evaluation metric
metric = load_metric("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(logits, dim=-1)
    return metric.compute(predictions=predictions, references=labels)

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Trainer for fine-tuning the model
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

# Train the model
trainer.train()

# Save the model for later use
model.save_pretrained('./controversy-model')
tokenizer.save_pretrained('./controversy-model')

# Example function to make predictions
def predict_controversy(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=-1)
    return "Controversial" if predictions.item() == 1 else "Not Controversial"

# Test the function
test_text = "This is a very controversial statement."
print(predict_controversy(test_text))