import json
import pickle
import numpy as np
import random

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD

import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

words = []
classes = []
documents = []
ignore_words = ['?', '!', '.', ',', '\'', '\"', '_', '-']
dialogs_file = open('dialogs.json').read()
dialogs = json.loads(dialogs_file)

for dialog in dialogs['dialogs']:
    for trigger in dialog['triggers']:
        w = nltk.word_tokenize(trigger)
        words.extend(w)
        documents.append((w, dialog['tag']))
        if dialog['tag'] not in classes:
            classes.append(dialog['tag'])

words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

print(len(documents), "documents")
print(len(classes), "classes", classes)
print(len(words), "unique lemmatized words", words)

pickle.dump(words, open('texts.pkl', 'wb'))
pickle.dump(classes, open('labels.pkl', 'wb'))

training = []

output_empty = [0] * len(classes)

for doc in documents:
    bag = []
    trigger_words = doc[0]
    trigger_words = [lemmatizer.lemmatize(word.lower()) for word in trigger_words]
    for w in words:
        bag.append(1) if w in trigger_words else bag.append(0)

    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1

    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training)

train_x = list(training[:, 0])
train_y = list(training[:, 1])
print("[Training] data created.")

'''
Create model - 3 layers. 
First layer 128 neurons
Second layer 64 neurons
Third output layer contains number of neurons

equal to number of dialogs to predict output dialog with softmax
'''

model = Sequential()
# 128 neurons, 'relu' = rectified linear unit
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
# 64 neurons
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))
# Compile model. Stochastic gradient descent with nesterov accelerated gradient gives good results for this model
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
# fitting and saving the model
hist = model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)

model.save('model.h5', hist)
print("[model] finished training.")

