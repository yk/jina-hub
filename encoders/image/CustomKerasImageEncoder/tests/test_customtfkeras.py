import pytest
import os

import numpy as np

from .. import CustomKerasImageEncoder
from jina.executors.metas import get_default_metas
from jina.executors import BaseExecutor
from jina.excepts import PretrainedModelFileDoesNotExist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Activation, Flatten, Dense


class TestNet:
    def __init__(self):
        self.model = None
        self.input_shape = (224, 224, 3)
        self.conv = Conv2D(32, (3, 3), padding='same', name='conv1', input_shape=self.input_shape)
        self.activation_relu = Activation('relu')
        self.flatten = Flatten()
        self.dense = Dense(10, name='dense')
        self.activation_softmax = Activation('softmax')

    def create_model(self):
        self.model = Sequential()
        self.model.add(self.conv)
        self.model.add(self.activation_relu)
        self.model.add(self.flatten)
        self.model.add(self.dense)
        self.model.add(self.activation_softmax)
        return self.model


def get_encoder(model_path_tmp_dir):
    metas = get_default_metas()
    if 'JINA_TEST_GPU' in os.environ:
        metas['on_gpu'] = True
        metas['workspace'] = model_path_tmp_dir
    path = os.path.join(model_path_tmp_dir, 'model.pth')
    model = TestNet().create_model()
    model.save(path)
    return CustomKerasImageEncoder(channel_axis=1, model_path=path, layer_name='dense', metas=metas)


def test_encoding_results(tmpdir):
    target_output_dim = 10
    input_dim = 224
    encoder = get_encoder(str(tmpdir))
    test_data = np.random.rand(2, 3, input_dim, input_dim).astype('float32')
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (2, target_output_dim)


def test_save_and_load(tmpdir):
    input_dim = 224
    encoder = get_encoder(str(tmpdir))
    test_data = np.random.rand(2, 3, input_dim, input_dim).astype('float32')
    encoded_data_control = encoder.encode(test_data)
    encoder.touch()
    encoder.save()
    assert os.path.exists(encoder.save_abspath)
    encoder_loaded = BaseExecutor.load(encoder.save_abspath)
    encoded_data_test = encoder_loaded.encode(test_data)
    assert encoder_loaded.channel_axis == encoder.channel_axis
    np.testing.assert_array_equal(encoded_data_control, encoded_data_test)


def test_raise_exception():
    with pytest.raises(PretrainedModelFileDoesNotExist):
        CustomKerasImageEncoder()
