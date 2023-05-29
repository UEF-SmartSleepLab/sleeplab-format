import argparse
import dataset
import numpy as np
import tensorflow as tf

from pathlib import Path


def conv_block(x, filters, kernel_size):
    x = tf.keras.layers.Conv1D(
        filters=filters, kernel_size=kernel_size, padding='SAME')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.activations.relu(x, alpha=0.1)

    x = tf.keras.layers.Conv1D(
        filters=filters, kernel_size=kernel_size, padding='SAME')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.activations.relu(x, alpha=0.1)

    x = tf.keras.layers.MaxPool1D(pool_size=2)(x)

    return x


def create_model(input_names, fs, n_classes=5):
    # Create and concatenate inputs
    inputs = []
    for input_name in input_names:
        inp = tf.keras.layers.Input(shape=(None, 1), name=input_name)
        inputs.append(inp)
    x = tf.keras.layers.Concatenate(name='concat_inputs')(inputs)

    # Create a number of conv blocks to downsample the input resolution from fs to 1Hz
    num_blocks = int(np.log2(fs))
    filters = 8
    kernel_size = 5
    for _ in range(num_blocks):
        x = conv_block(x, filters, kernel_size)
        filters *= 2  # Double the number of features on each block

    # Use avg pooling to downsample the 1Hz signals to 30s epochs
    x = tf.keras.layers.AvgPool1D(pool_size=30)(x)

    # Finally, reduce the channels of the 30-segments to n_classes, and use softmax activation
    x = tf.keras.layers.Conv1D(
        filters=n_classes, kernel_size=1, activation='softmax', padding='SAME', name='hypnogram'
    )(x)

    return tf.keras.Model(inputs=inputs, outputs=[x], name='simple_cnn')


def training_loop(model_dir, epochs, fs=64.0, batch_size=5):
    # Create the datasets
    datasets = dataset.load_datasets(dataset.dataset_config)
    output_names = ['hypnogram']
    input_names = list(set(dataset.component_config.keys()) - set(output_names))

    # Map the datasets to input and output
    def _io_map_func(d):
        inputs = {k: d[k] for k in input_names}
        outputs = {k: tf.expand_dims(d[k], -1) for k in output_names}
        return inputs, outputs

    train_size = len(datasets['train'])
    train_ds = (datasets['train']
        .map(_io_map_func)
        .shuffle(3 * batch_size)
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
        .repeat()
    )
    val_size = len(datasets['val'])
    val_ds = (datasets['val']
        .map(_io_map_func)
        .batch(1)
        .prefetch(tf.data.AUTOTUNE)
        .repeat()
    )
    test_size = len(datasets['test'])
    test_ds = (datasets['test']
        .map(_io_map_func)
        .batch(1)
        .prefetch(tf.data.AUTOTUNE)
        .repeat()
    )

    # Create the model
    m = create_model(input_names=input_names, fs=fs)
    loss = 'sparse_categorical_crossentropy'
    optimizer = tf.keras.optimizers.experimental.AdamW()
    m.compile(optimizer=optimizer, loss=loss,
              metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])

    # Define training callbacks
    cbs = []
    ckpt_path = Path(model_dir) / 'dod_best_model'
    cbs.append(tf.keras.callbacks.ModelCheckpoint(
        ckpt_path, monitor='val_loss', save_best_only=True
    ))

    # Train the model
    train_steps = train_size // batch_size
    m.fit(
        train_ds,
        steps_per_epoch=train_steps,
        epochs=epochs,
        validation_data=val_ds,
        validation_steps=val_size,
        callbacks=cbs,
        verbose=1
    )

    # Evaluate
    best_m = tf.keras.models.load_model(ckpt_path)
    best_m.evaluate(test_ds, steps=test_size)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir')
    parser.add_argument('--epochs', type=int, default=3)
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    training_loop(model_dir=args.model_dir, epochs=args.epochs)
