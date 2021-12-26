"""Self Attention and Intersample Attention blocks with TensorFlow"""

from typing import Callable, Dict, Union
import tensorflow as tf


def MLP(
    hidden_dim: int,
    output_dim: int,
    output_activation: Union[str, Callable] = None,
    kernel_initializer: Union[str, Callable] = "glorot_uniform",
    bias_initializer: Union[str, Callable] = "zeros",
    kernel_regularizer: Union[str, Callable] = None,
    bias_regularizer: Union[str, Callable] = None,
    activity_regularizer: Union[str, Callable] = None,
    kernel_constraint: Union[str, Callable] = None,
    bias_constraint: Union[str, Callable] = None,
    **kwargs,
):
    """[summary]

    Args:
        hidden_dim (int): [description]
        output_dim (int): [description]
        output_activation (Union[str, Callable]): [description]
        kernel_initializer (Union[str, Callable], optional): [description]. Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): [description]. Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        bias_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        activity_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        kernel_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        bias_constraint (Union[str, Callable], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """
    return tf.keras.Sequential(
        [
            tf.keras.layers.Dense(
                units=hidden_dim,
                activation="relu",
                use_bias=True,
                kernel_initializer=kernel_initializer,
                bias_initializer=bias_initializer,
                kernel_regularizer=kernel_regularizer,
                bias_regularizer=bias_regularizer,
                activity_regularizer=activity_regularizer,
                kernel_constraint=kernel_constraint,
                bias_constraint=bias_constraint,
                **kwargs,
            ),
            tf.keras.layers.Dense(
                units=output_dim,
                activation=output_activation,
                use_bias=True,
                kernel_initializer=kernel_initializer,
                bias_initializer=bias_initializer,
                kernel_regularizer=kernel_regularizer,
                bias_regularizer=bias_regularizer,
                activity_regularizer=activity_regularizer,
                kernel_constraint=kernel_constraint,
                bias_constraint=bias_constraint,
                **kwargs,
            ),
        ]
    )


class SelfAttentionBlock(tf.keras.layers.Layer):
    """[summary]

    Args:
        num_heads (int): [description]
        embed_dim (int): [description]
        hidden_dim (int): [description]
        kernel_initializer (Union[str, Callable], optional): [description]. Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): [description]. Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        bias_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        kernel_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        bias_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        dropout (float, optional): [description]. Defaults to 0.1.
        epsilon (float, optional): [description]. Defaults to 1e-6.
    """

    def __init__(
        self,
        num_heads: int,
        embed_dim: int,
        hidden_dim: int,
        kernel_initializer: Union[str, Callable] = "glorot_uniform",
        bias_initializer: Union[str, Callable] = "zeros",
        kernel_regularizer: Union[str, Callable] = None,
        bias_regularizer: Union[str, Callable] = None,
        kernel_constraint: Union[str, Callable] = None,
        bias_constraint: Union[str, Callable] = None,
        dropout: float = 0.1,
        epsilon: float = 1e-6,
        **kwargs,
    ):
        super(SelfAttentionBlock, self).__init__(**kwargs)

        self.num_heads = num_heads
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim

        self.kernel_initializer = tf.keras.initializers.get(kernel_initializer)
        self.kernel_regularizer = tf.keras.regularizers.get(kernel_regularizer)
        self.kernel_constraint = tf.keras.constraints.get(kernel_constraint)

        self.bias_initializer = tf.keras.initializers.get(bias_initializer)
        self.bias_regularizer = tf.keras.regularizers.get(bias_regularizer)
        self.bias_constraint = tf.keras.constraints.get(bias_constraint)

        self.epsilon = epsilon
        self.dropout = dropout

        self.set_inner_layers()

    def set_inner_layers(self):
        """Define Self Attention/Transformer block layers."""

        self.attention_layer = tf.keras.layers.MultiHeadAttention(
            num_heads=self.num_heads,
            key_dim=self.embed_dim,
            dropout=self.dropout,
            use_bias=True,
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
        )

        self.feed_forward_network = MLP(
            hidden_dim=self.hidden_dim,
            output_dim=self.embed_dim,
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
        )

        self.layer_norm1 = tf.keras.layers.LayerNormalization(epsilon=self.epsilon)
        self.layer_norm2 = tf.keras.layers.LayerNormalization(epsilon=self.epsilon)

        self.dropout1 = tf.keras.layers.Dropout(rate=self.dropout)
        self.dropout2 = tf.keras.layers.Dropout(rate=self.dropout)

    def call(self, inputs: tf.Tensor, training: bool, mask: tf.Tensor) -> tf.Tensor:
        """[summary]

        Args:
            inputs (tf.Tensor): [description]
            training (bool): [description]
            mask (tf.Tensor): [description]

        Returns:
            tf.Tensor: [description]
        """
        attention_output = self.compute_attention(
            inputs, training=training, attention_mask=mask
        )
        attention_output = self.dropout1(attention_output, training=training)
        output1 = self.layer_norm1(inputs + attention_output)

        output2 = self.feed_forward_network(output1)
        output2 = self.dropout2(output2, training=training)

        return self.layer_norm2(output1 + output2)

    def compute_attention(
        self, inputs: tf.Tensor, training: bool, attention_mask: tf.Tensor
    ) -> tf.Tensor:
        return self.attention_layer(
            inputs, inputs, training=training, attention_mask=attention_mask
        )

    @classmethod
    def from_config(cls, config):
        """[summary]

        Args:
            config ([type]): [description]

        Returns:
            [type]: [description]
        """
        config["kernel_initializer"] = tf.keras.initializers.deserialize(
            config["kernel_initializer"]
        )
        config["bias_initializer"] = tf.keras.initializers.deserialize(
            config["bias_initializer"]
        )
        config["kernel_regularizer"] = tf.keras.regularizers.deserialize(
            config["kernel_regularizer"]
        )
        config["bias_regularizer"] = tf.keras.regularizers.deserialize(
            config["bias_regularizer"]
        )
        config["kernel_constraint"] = tf.keras.constraints.deserialize(
            config["kernel_constraint"]
        )
        config["bias_constraint"] = tf.keras.constraints.deserialize(
            config["bias_constraint"]
        )
        return cls(**config)

    def get_config(self) -> dict:
        base_config = super(SelfAttentionBlock, self).get_config()
        config = {
            "num_heads": self.num_heads,
            "embed_dim": self.embed_dim,
            "hidden_dim": self.hidden_dim,
            "kernel_initializer": tf.keras.initializers.serialize(
                self.kernel_initializer
            ),
            "bias_initializer": tf.keras.initializers.serialize(self.bias_initializer),
            "kernel_regularizer": self.tf.keras.regularizers.serialize(
                self.kernel_regularizer
            ),
            "bias_regularizer": self.tf.keras.regularizers.serialize(
                self.bias_regularizer
            ),
            "kernel_constraint": self.tf.keras.constraints.serialize(
                self.kernel_constraint
            ),
            "bias_constraint": self.tf.keras.constraints.serialize(
                self.bias_constraint
            ),
            "dropout": self.dropout,
            "epsilon": self.epsilon,
        }
        return dict(list(base_config.items()) + list(config.items()))


class IntersampleAttentionBlock(SelfAttentionBlock):
    """[summary]

    Args:
        num_heads (int): [description]
        embed_dim (int): [description]
        hidden_dim (int): [description]
        kernel_initializer (Union[str, Callable], optional): [description]. Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): [description]. Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        bias_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        kernel_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        bias_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        dropout (float, optional): [description]. Defaults to 0.1.
        epsilon (float, optional): [description]. Defaults to 1e-6.
    """

    def compute_attention(
        self, inputs: tf.Tensor, training: bool, attention_mask: tf.Tensor
    ) -> tf.Tensor:
        """Intersample Attention operation.

        Args:
            inputs (tf.Tensor): [description]
            training (bool): [description]
            attention_mask (tf.Tensor): [description]

        Returns:
            tf.Tensor: [description]
        """
        batch, n_samples, feature_dim = inputs.shape
        reshaped_inputs = tf.reshape(inputs, (1, batch, n_samples * feature_dim))

        attention_output = self.attention_layer(
            reshaped_inputs,
            reshaped_inputs,
            training=training,
            attention_mask=attention_mask,
        )
        output = tf.reshape(attention_output, (batch, n_samples, feature_dim))
        return output


def SAINTBlock(
    embed_dim: int,
    num_heads: int,
    hidden_dim: int,
    kernel_initializer: Union[str, Callable] = "glorot_uniform",
    bias_initializer: Union[str, Callable] = "zeros",
    kernel_regularizer: Union[str, Callable] = None,
    bias_regularizer: Union[str, Callable] = None,
    kernel_constraint: Union[str, Callable] = None,
    bias_constraint: Union[str, Callable] = None,
    dropout: float = 0.1,
    epsilon: float = 1e-6,
    **kwargs,
):
    """[summary]

    Args:
        embed_dim (int): [description]
        num_heads (int): [description]
        hidden_dim (int): [description]
        kernel_initializer (Union[str, Callable], optional): [description]. Defaults to "glorot_uniform".
        bias_initializer (Union[str, Callable], optional): [description]. Defaults to "zeros".
        kernel_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        bias_regularizer (Union[str, Callable], optional): [description]. Defaults to None.
        kernel_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        bias_constraint (Union[str, Callable], optional): [description]. Defaults to None.
        dropout (float, optional): [description]. Defaults to 0.1.
        epsilon (float, optional): [description]. Defaults to 1e-6.

    Returns:
        [type]: [description]
    """
    return tf.keras.Sequential(
        [
            SelfAttentionBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                hidden_dim=hidden_dim,
                kernel_initializer=kernel_initializer,
                bias_initializer=bias_initializer,
                kernel_regularizer=kernel_regularizer,
                bias_regularizer=bias_regularizer,
                kernel_constraint=kernel_constraint,
                bias_constraint=bias_constraint,
                dropout=dropout,
                epsilon=epsilon,
                **kwargs,
            ),
            IntersampleAttentionBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                hidden_dim=hidden_dim,
                kernel_initializer=kernel_initializer,
                bias_initializer=bias_initializer,
                kernel_regularizer=kernel_regularizer,
                bias_regularizer=bias_regularizer,
                kernel_constraint=kernel_constraint,
                bias_constraint=bias_constraint,
                dropout=dropout,
                epsilon=epsilon,
                **kwargs,
            ),
        ]
    )