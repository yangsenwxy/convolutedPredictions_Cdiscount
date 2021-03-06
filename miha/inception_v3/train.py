import os
import pickle

from keras.applications.inception_v3 import InceptionV3
from keras.layers import Flatten, Dense, AveragePooling2D, Dropout, GlobalAveragePooling2D
from keras.models import Model
from keras.optimizers import RMSprop, Adam, SGD
from keras.callbacks import ModelCheckpoint
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
import math

from keras.models import load_model
import keras.backend as K
from keras.metrics import top_k_categorical_accuracy
import tensorflow as tf

from multiGPU import MultiGPUModel
import numpy as np

import sys

sys.path = ["/shared/miha/ws/competitions/p18french/"] + sys.path
from fetch_generators import get_custom_gen

model_name = "inceptionv3_v3"
models_savename = "./models/" + model_name

train_data_dir = '/workspace6/miha_misc2/train/'
val_data_dir = '/workspace6/miha_misc2/val/'
classnames = pickle.load(open("/workspace6/miha_misc2/class_order.pkl", "rb"))
batch_size = 300
img_width = 180
img_height = 180


# Data generator
def train_preprocess(x):
    a, b = np.random.randint(0, 21, (2))
    x = x[a:a + 160, b:b + 160]
    return ((x / 255.) - 0.5) * 2


def test_preprocess(x):
    x = x[10:170, 10:170]
    return ((x / 255.) - 0.5) * 2


print("Importing pre-processors")
train_datagen = ImageDataGenerator(
    preprocessing_function=train_preprocess,
    horizontal_flip=True)
train_generator = get_custom_gen("../generator_train_v1.pkl", train_datagen, batch_size=batch_size,
                                 target_size=img_width)

val_datagen = ImageDataGenerator(preprocessing_function=test_preprocess)
validation_generator = get_custom_gen("../generator_val1_v1.pkl", val_datagen, batch_size=batch_size,
                                      target_size=img_width)

print("Importing models")
model0 = InceptionV3(include_top=False, weights='imagenet',
                     input_tensor=None, input_shape=(160, 160, 3))

for lay in model0.layers:
    lay.trainable = False

x = model0.output
x = GlobalAveragePooling2D(name='avg_pool')(x)
x = Dense(3000, activation='relu', name='fc1')(x)
x = Dropout(0.5)(x)
x = Dense(len(classnames), activation='softmax', name='predictions')(x)
model0 = Model(model0.input, x)

model = MultiGPUModel(model0, [0, 1], int(batch_size / 2))


os.makedirs("./models", exist_ok=True)
callbacks = [ModelCheckpoint(monitor='val_loss',
                             filepath=models_savename + '_{epoch:03d}-{val_loss:.7f}.hdf5',
                             save_best_only=False,
                             save_weights_only=False,
                             mode='max'),
             TensorBoard(log_dir='logs/{}'.format(model_name))]


model.compile(loss='categorical_crossentropy', optimizer=SGD(lr=0.001, momentum=0.9),
              metrics=[top_k_categorical_accuracy, 'accuracy'])


model.fit_generator(generator=train_generator,
                    steps_per_epoch=math.ceil(2000000 / batch_size),
                    verbose=1,
                    callbacks=callbacks,
                    validation_data=validation_generator,
                    initial_epoch=0,
                    epochs=3,
                    use_multiprocessing=True,
                    max_queue_size=10,
                    workers=16,
                    validation_steps=math.ceil(10000 / batch_size))


for clayer in model.layers[3].layers:
    clayer.trainable = True

# train first part
model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.00025),
              metrics=[top_k_categorical_accuracy, 'accuracy'])
model.fit_generator(generator=train_generator,
                    steps_per_epoch=math.ceil(2000000 / batch_size),
                    verbose=1,
                    callbacks=callbacks,
                    validation_data=validation_generator,
                    initial_epoch=3,
                    epochs=15,
                    use_multiprocessing=True,
                    max_queue_size=10,
                    workers=16,
                    validation_steps=math.ceil(10000 / batch_size))


model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.0002),
              metrics=[top_k_categorical_accuracy, 'accuracy'])

model.fit_generator(generator=train_generator,
                    steps_per_epoch=math.ceil(2000000 / batch_size),
                    verbose=1,
                    callbacks=callbacks,
                    validation_data=validation_generator,
                    initial_epoch=15,
                    epochs=30,
                    use_multiprocessing=True,
                    max_queue_size=10,
                    workers=16,
                    validation_steps=math.ceil(10000 / batch_size))

model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.000175),
              metrics=[top_k_categorical_accuracy, 'accuracy'])

model.fit_generator(generator=train_generator,
                    steps_per_epoch=math.ceil(2000000 / batch_size),
                    verbose=1,
                    callbacks=callbacks,
                    validation_data=validation_generator,
                    initial_epoch=30,
                    epochs=45,
                    use_multiprocessing=True,
                    max_queue_size=10,
                    workers=16,
                    validation_steps=math.ceil(10000 / batch_size))

model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.0001),
              metrics=[top_k_categorical_accuracy, 'accuracy'])

model.fit_generator(generator=train_generator,
                    steps_per_epoch=math.ceil(2000000 / batch_size),
                    verbose=1,
                    callbacks=callbacks,
                    validation_data=validation_generator,
                    initial_epoch=45,
                    epochs=51,
                    use_multiprocessing=True,
                    max_queue_size=10,
                    workers=16,
                    validation_steps=math.ceil(10000 / batch_size))


model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.00008),
              metrics=['accuracy'])
model.fit_generator(steps_per_epoch=math.ceil(2000000 / batch_size),
          verbose=1,
          callbacks=callbacks,
          initial_epoch=51,
          epochs=70,
          max_queue_size=10,
          workers=16,
          validation_steps=math.ceil(10000 / batch_size),
          generator=train_generator,
          validation_data=validation_generator)


model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.00006),
              metrics=['accuracy'])

model.fit_generator(steps_per_epoch=math.ceil(2000000 / batch_size),
          verbose=1,
          callbacks=callbacks,
          initial_epoch=70,
          epochs=80,
          max_queue_size=10,
          workers=16,
          validation_steps=math.ceil(10000 / batch_size),
          generator=train_generator,
          validation_data=validation_generator)

model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.00004),
              metrics=['accuracy'])


model.fit(steps_per_epoch=math.ceil(2000000 / batch_size),
          verbose=1,
          callbacks=callbacks,
          initial_epoch=80,
          epochs=81,
          max_queue_size=10,
          workers=16,
          validation_steps=math.ceil(10000 / batch_size),
          generator=train_generator,
          validation_data=validation_generator)

callbacks = [ModelCheckpoint(monitor='val_loss',
                             filepath= models_savename + '_{epoch:03d}-{loss:.7f}.hdf5',
                             save_best_only=False,
                             save_weights_only=False,
                             mode='max'),
             TensorBoard(log_dir='logs/{}'.format(model_name))]



model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.00004),
              metrics=['accuracy'])


model.fitgenerator(steps_per_epoch=math.ceil(2000000 / batch_size),
          verbose=1,
          callbacks=callbacks,
          initial_epoch=81,
          epochs=99,
          max_queue_size=10,
          workers=16,
          validation_steps=math.ceil(10000 / batch_size),
          generator=train_generator,
          validation_data=validation_generator)
