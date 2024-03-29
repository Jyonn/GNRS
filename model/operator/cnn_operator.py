import torch
from torch import nn

from loader.global_setting import Setting
from model.common.attention import AdditiveAttention
from model.inputer.simple_inputer import SimpleInputer
from model.operator.base_operator import BaseOperatorConfig, BaseOperator


class CNNOperatorConfig(BaseOperatorConfig):
    def __init__(
            self,
            kernel_size: int = 3,
            dropout: float = 0.1,
            additive_hidden_size: int = 256,
            **kwargs,
    ):
        super().__init__(**kwargs)

        self.kernel_size = kernel_size
        self.dropout = dropout
        self.additive_hidden_size = additive_hidden_size


class CNNOperator(BaseOperator):
    config_class = CNNOperatorConfig
    config: CNNOperatorConfig
    inputer_class = SimpleInputer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.target_user:
            embed_dim = self.config.hidden_size
        else:
            embed_dim = self.config.embed_hidden_size

        self.cnn = nn.Conv1d(
            in_channels=embed_dim,
            out_channels=self.config.hidden_size,
            kernel_size=self.config.kernel_size,
            padding='same',
        )
        self.linear = nn.Linear(embed_dim, self.config.hidden_size)
        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(self.config.dropout)

        self.additive_attention = AdditiveAttention(
            embed_dim=self.config.hidden_size,
            hidden_size=self.config.additive_hidden_size,
        )

    def forward(self, embeddings: dict, mask=None, **kwargs):
        output_list = []
        output_mask = []
        for col in embeddings:
            embedding = embeddings[col]
            if embedding.size()[1] > 1:
                embedding = self.cnn(embedding.permute(0, 2, 1))
                activation = self.activation(embedding.permute(0, 2, 1))
                masked_activation = activation * mask[col].unsqueeze(-1).to(Setting.device)
                output = self.dropout(masked_activation)
            else:
                # output = embedding
                output = self.linear(embedding)
            output_list.append(output)
            output_mask.append(mask[col])

        outputs = torch.cat(output_list, dim=1).to(Setting.device)
        mask = torch.cat(output_mask, dim=1).to(Setting.device)
        outputs = self.additive_attention(outputs, mask)
        return outputs
